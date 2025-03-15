from flask import Blueprint, render_template, redirect, url_for, request, session, flash, jsonify
from app import db
from app.models.user import User
from app.models.skill import Skill
from app.models.audit import AuditLog
from app.utils.file_helpers import allowed_file
from werkzeug.utils import secure_filename
import os
from datetime import datetime

skills_bp = Blueprint('skills', __name__)

@skills_bp.route('/skills', methods=['GET', 'POST'])
def manage_skills():
    if 'user_id' not in session:
        # Ensure the user is logged in and authorized
        return redirect(url_for('auth.login_user'))

    user = User.query.get(session['user_id'])

    # Handle adding a new skill
    if request.method == 'POST':
        skill_name = request.form.get('skill_name')
        proficiency = request.form.get('proficiency')
        certificate = request.files.get('certificate')

        # Validate skill inputs
        if not skill_name or not proficiency:
            return redirect(url_for('skills.manage_skills'))

        # Handle certificate upload if a file is provided
        certificate_path = None
        if certificate and allowed_file(certificate.filename):
            try:
                # Secure the filename
                certificate_filename = secure_filename(certificate.filename)

                # Get the upload folder path
                upload_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'static', 'uploads')
                os.makedirs(upload_folder, exist_ok=True)

                # Save the file inside the static/uploads folder
                certificate_path = os.path.join(upload_folder, certificate_filename)
                certificate.save(certificate_path)

                # Normalize the path to use forward slashes for URLs
                certificate_path = os.path.normpath(certificate_path).replace("\\", "/")

            except Exception as e:
                return redirect(url_for('skills.manage_skills'))

        # Add the new skill to the database
        try:
            # Extract the relative path for database storage
            relative_path = None
            if certificate_path:
                relative_path = os.path.basename(certificate_path)
                
            new_skill = Skill(
                skill_name=skill_name,
                proficiency=proficiency,
                user_id=user.user_id,
                certificate_path=relative_path
            )
            db.session.add(new_skill)

            # Log the action in the audit logs
            new_log = AuditLog(
                user_id=user.user_id,
                action=f'Added new skill: {skill_name}, Proficiency: {proficiency}.'
            )
            db.session.add(new_log)
            db.session.commit()

        except Exception as e:
            db.session.rollback()  # Rollback the session in case of any error
            return redirect(url_for('skills.manage_skills'))

        return redirect(url_for('skills.manage_skills'))

    # Query all skills for the current user
    user_skills = Skill.query.filter_by(user_id=user.user_id).all()
    return render_template('skills.html', user_skills=user_skills)

@skills_bp.route('/edit_skill/<int:skill_id>', methods=['GET', 'POST'])
def edit_skill(skill_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login_user'))

    skill = Skill.query.get_or_404(skill_id)

    # Ensure the user is authorized to edit the skill
    if skill.user_id != session['user_id'] and session.get('role') != 'admin':
        # Log the unauthorized attempt
        new_log = AuditLog(
            user_id=session['user_id'],
            action=f'Attempted to edit a skill they do not own (Skill ID: {skill_id}).'
        )
        db.session.add(new_log)
        db.session.commit()

        return redirect(url_for('skills.manage_skills'))

    if request.method == 'POST':
        skill_name = request.form['skill_name']
        proficiency = request.form['proficiency']
        certificate = request.files.get('certificate')

        # Handle certificate upload if a file is provided
        certificate_path = skill.certificate_path  # Preserve the current certificate path

        if certificate and allowed_file(certificate.filename):
            # Secure the filename
            certificate_filename = secure_filename(certificate.filename)
            
            # Get the upload folder path
            upload_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'static', 'uploads')
            os.makedirs(upload_folder, exist_ok=True)

            # Save the certificate file to the uploads folder
            certificate_path = os.path.join(upload_folder, certificate_filename)
            certificate.save(certificate_path)

            # Extract the relative path for database storage
            certificate_path = os.path.basename(certificate_path)

        # Update the skill information
        skill.skill_name = skill_name
        skill.proficiency = proficiency
        if certificate and allowed_file(certificate.filename):
            skill.certificate_path = certificate_path

        db.session.commit()

        # Log the skill update action
        new_log = AuditLog(
            user_id=session['user_id'],
            action=f'Updated skill (ID: {skill_id}): {skill_name}, Proficiency: {proficiency}.'
        )
        db.session.add(new_log)
        db.session.commit()

        return redirect(url_for('skills.manage_skills'))

    return render_template('edit_skill.html', skill=skill)

@skills_bp.route('/delete_skill/<int:skill_id>', methods=['POST'])
def delete_skill(skill_id):
    # Check if the user is logged in
    if 'user_id' not in session:
        return redirect(url_for('auth.login_user'))

    # Find the skill by ID or return a 404 if not found
    skill_to_delete = Skill.query.get_or_404(skill_id)

    # Ensure the logged-in user owns the skill or is an admin
    if skill_to_delete.user_id == session['user_id'] or session.get('role') == 'admin':
        try:
            db.session.delete(skill_to_delete)
            db.session.commit()

            # Log the skill deletion
            new_log = AuditLog(
                user_id=session['user_id'],
                action=f'Deleted skill (ID: {skill_id}).'
            )
            db.session.add(new_log)
            db.session.commit()

        except Exception as e:
            db.session.rollback()  # Rollback in case of error
    else:
        # Log the unauthorized deletion attempt
        new_log = AuditLog(
            user_id=session['user_id'],
            action=f'Attempted to delete a skill they do not own (Skill ID: {skill_id}).'
        )
        db.session.add(new_log)
        db.session.commit()

    # Redirect to the skills management page
    return redirect(url_for('skills.manage_skills'))
