from flask import Blueprint, render_template, redirect, url_for, request, session, flash, jsonify
from app import db
from app.models.user import User
from app.models.audit import AuditLog
from app.models.project import Project
from app.models.skill import Skill
from app.models.notification import Notification
from app.models.friendship import FriendRequest
from sqlalchemy import text
from datetime import datetime
import os
from flask_migrate import upgrade, init, migrate, stamp
from sqlalchemy.exc import ProgrammingError

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin_dashboard')
def admin_dashboard():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('auth.login_user'))

    # Query the database to get all users, projects, and skills
    users = User.query.all()
    projects = Project.query.all()
    skills = Skill.query.all()
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).all()
    
    # Create a dictionary for user lookup
    user_dict = {user.user_id: user for user in users}
    
    return render_template('admin_dashboard.html', logs=logs, users=users, 
                          projects=projects, skills=skills, user_dict=user_dict)

@admin_bp.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('auth.login_user'))

    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        old_name = user.name
        old_email = user.email
        old_role = user.role

        # Update the user's details
        user.name = request.form['name']
        user.email = request.form['email']
        user.role = request.form['role']
        db.session.commit()

        # Log the action in Audit Logs
        changed_fields = []
        if old_name != user.name:
            changed_fields.append(f'Name changed from {old_name} to {user.name}')
        if old_email != user.email:
            changed_fields.append(f'Email changed from {old_email} to {user.email}')
        if old_role != user.role:
            changed_fields.append(f'Role changed from {old_role} to {user.role}')

        # Create a log entry for the edit action
        change_description = ', '.join(changed_fields) if changed_fields else 'User details updated'
        new_log = AuditLog(
            user_id=session.get('user_id'),
            action=f'Edited user details: {change_description}'
        )
        db.session.add(new_log)
        db.session.commit()

        return redirect(url_for('admin.admin_dashboard'))

    return render_template('edit_user.html', user=user)

@admin_bp.route('/delete_user/<int:user_id>', methods=['POST', 'DELETE'])
def delete_user(user_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Unauthorized access. Please log in as an admin.', 'danger')
        return redirect(url_for('auth.login_user'))

    user = User.query.get(user_id)
    if not user:
        return redirect(url_for('admin.admin_dashboard'))

    # Delete notifications related to the user
    Notification.query.filter(Notification.sender_id == user_id).delete()

    # Reassign projects to a default admin user or another valid user
    default_admin_id = 1  # Replace with a valid admin user ID
    FriendRequest.query.filter(
        (FriendRequest.sender_id == user_id) | (FriendRequest.receiver_id == user_id)
    ).delete()

    user_projects = Project.query.filter_by(created_by=user_id).all()
    for project in user_projects:
        project.created_by = default_admin_id

    # Log the deletion action
    new_log = AuditLog(
        user_id=session.get('user_id'),
        action=f'Deleted user: {user.name} with email {user.email}.'
    )
    db.session.add(new_log)

    # Delete the user
    db.session.delete(user)
    db.session.commit()

    flash('User deleted successfully!', 'success')
    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/users', methods=['GET', 'POST'])
def manage_users():
    if 'role' not in session or session.get('role') != 'admin':
        return redirect(url_for('auth.login_user'))

    if request.method == 'POST':
        # Add a new user
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = request.form.get('role', 'student')
        bio = request.form.get('bio', None)
        profile_picture = request.form.get('profile_picture', None)

        # Check if user with the same email already exists
        if User.query.filter_by(email=email).first():
            return redirect(url_for('admin.manage_users'))

        # Check if user with the same username already exists
        if User.query.filter_by(name=name).first():
            return redirect(url_for('admin.manage_users'))

        # Hash the password
        from werkzeug.security import generate_password_hash
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(
            name=name,
            email=email,
            password_hash=hashed_password,
            role=role,
            bio=bio,
            profile_picture=profile_picture
        )
        db.session.add(new_user)
        db.session.commit()

        # Log the action in Audit Logs
        new_log = AuditLog(
            user_id=session.get('user_id'),
            action=f'Created a new user: {name} with email {email}.'
        )
        db.session.add(new_log)
        db.session.commit()

        return redirect(url_for('admin.manage_users'))

    # Query all users from the database
    all_users = User.query.all()
    return render_template('users.html', users=all_users)

@admin_bp.route('/admin_query', methods=['GET', 'POST'])
def admin_query():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('auth.login_user'))

    if request.method == 'POST':
        try:
            query = request.form.get('query')
            if not query:
                return jsonify({"error": "No query provided"}), 400
                
            # Basic security check - prevent schema modifications
            lower_query = query.lower().strip()
            disallowed_keywords = ['drop', 'alter', 'truncate', 'delete from', 'update', 'grant', 'revoke']
            
            # Allow PRAGMA commands for table schema information
            if not lower_query.startswith('pragma') and any(keyword in lower_query for keyword in disallowed_keywords):
                return jsonify({"error": "This query type is not allowed for security reasons"}), 403

            try:
                # Log the query attempt
                new_log = AuditLog(
                    user_id=session.get('user_id'),
                    action=f'Executed database query: {query[:50]}{"..." if len(query) > 50 else ""}'
                )
                db.session.add(new_log)
                db.session.commit()
                
                # Execute the query safely using SQLAlchemy's text function
                result = db.session.execute(text(query))
                
                # For non-SELECT queries, commit and return success message
                if not lower_query.startswith('select') and not lower_query.startswith('pragma'):
                    db.session.commit()
                    affected_rows = result.rowcount if hasattr(result, 'rowcount') else 0
                    return jsonify({"message": f"Query executed successfully. Affected rows: {affected_rows}"})
                
                # For SELECT and PRAGMA queries, return results
                rows = result.fetchall()
                
                # Convert the rows into dictionaries
                columns = result.keys()
                result_list = [dict(zip(columns, row)) for row in rows]

                return jsonify(result_list)
            
            except Exception as e:
                db.session.rollback()
                return jsonify({"error": str(e)})
        
        except Exception as e:
            print(f"Error in admin_query: {str(e)}")
            db.session.rollback()
            return jsonify({"error": str(e)}), 500

    return render_template('admin_query.html')

@admin_bp.route('/get_tables', methods=['GET'])
def get_tables():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('auth.login_user'))
    try:
        result = db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
        tables = result.fetchall()
        return jsonify({'tables': [table[0] for table in tables]})
    except Exception as e:
        print(f"Error fetching tables: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/run_migrations/<secret_key>')
def run_migrations(secret_key):
    """Admin endpoint to manually run database migrations.
    Secured with a secret key that should match the MIGRATION_SECRET env variable."""
    
    # Only allow access with the correct secret key
    env_secret = os.environ.get('MIGRATION_SECRET', 'migration-secret-key')
    if secret_key != env_secret:
        return jsonify({"error": "Unauthorized"}), 401
    
    # Check if the user is an admin
    if 'user_id' in session and session.get('role') == 'admin':
        try:
            # Check if alembic_version table exists
            try:
                db.session.execute(db.text("SELECT * FROM alembic_version"))
                # If it exists, run migrations
                upgrade()
                return jsonify({"message": "Migrations completed successfully"})
            except ProgrammingError:
                # Initialize migrations
                init()
                migrate(message="Initial migration")
                stamp()
                return jsonify({"message": "Migration system initialized"})
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"error": "Admin access required"}), 403

@admin_bp.route('/create_admin/<secret_key>')
def create_admin_endpoint(secret_key):
    """Endpoint to manually create the default admin user."""
    
    # Verify secret key (same as migration secret or a specific admin creation secret)
    env_secret = os.environ.get('MIGRATION_SECRET', 'migration-secret-key')
    if secret_key != env_secret:
        return jsonify({"error": "Unauthorized - Invalid secret key"}), 401
    
    # Call the admin creation function
    from app.init_admin import create_default_admin
    success, message = create_default_admin()
    
    if success:
        # Log the successful admin creation
        new_log = AuditLog(
            user_id=1,  # Use ID 1 as it's usually the admin
            action="Created default admin user via API endpoint"
        )
        try:
            db.session.add(new_log)
            db.session.commit()
        except Exception as e:
            # Don't worry if logging fails
            print(f"Failed to log admin creation: {str(e)}")
    
    return jsonify({
        "success": success,
        "message": message
    })
