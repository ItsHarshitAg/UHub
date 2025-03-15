from flask import Blueprint, render_template, redirect, url_for, request, flash, session, jsonify, current_app
from app import db, bcrypt
from app.models.user import User
from app.models.audit import AuditLog
from werkzeug.utils import secure_filename
import os
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login_user():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        try:
            current_app.logger.debug(f"Attempting to log in user with email: {email}")
            # Find user by email
            user = User.query.filter_by(email=email).first()
            
            if user:
                current_app.logger.debug(f"User found: {user.name}")
            else:
                current_app.logger.debug("User not found")
            
            # Check if user exists and password matches (hashed comparison)
            if user and user.check_password(password):
                current_app.logger.debug("Password check passed")
                # Store user information in session
                session['user_id'] = user.user_id
                session['user_name'] = user.name
                session['role'] = user.role
                
                # Update last login time
                user.last_login = datetime.utcnow()
                db.session.commit()
                
                # Log the successful login
                log_entry = AuditLog(
                    user_id=user.user_id,
                    action="User logged in"
                )
                db.session.add(log_entry)
                db.session.commit()
                
                # Return JSON if this is an API request
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({
                        'status': 'success',
                        'message': 'Login successful!',
                        'redirect': url_for('user.user_dashboard')
                    })
                
                flash('Login successful!', 'success')
                return redirect(url_for('user.user_dashboard'))
            else:
                current_app.logger.debug("Invalid email or password")
                # Failed login attempt
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({
                        'status': 'error',
                        'message': 'Invalid email or password!'
                    }), 401
                
                flash('Invalid email or password!', 'danger')
                return redirect(url_for('auth.login_user'))
                
        except Exception as e:
            current_app.logger.error(f"Login error: {e}")
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'status': 'error',
                    'message': 'An error occurred during login.'
                }), 500
            else:
                flash('An error occurred during login.', 'danger')
                return redirect(url_for('auth.login_user'))
    
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register_user():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role', 'student')
        bio = request.form.get('bio', '')
        
        current_app.logger.debug(f"Attempting to register user with email: {email}")
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            current_app.logger.debug("Email already registered")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'status': 'error',
                    'message': 'Email already registered!'
                }), 400
            
            flash('Email already registered!', 'danger')
            return redirect(url_for('auth.register_user'))
        
        # Handle profile picture upload
        profile_picture = None
        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                upload_path = os.path.join('static', 'uploads')
                os.makedirs(upload_path, exist_ok=True)
                file.save(os.path.join(upload_path, filename))
                profile_picture = filename
        
        # Create new user with hashed password
        new_user = User(
            name=name,
            email=email,
            role=role,
            bio=bio,
            profile_picture=profile_picture,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        new_user.set_password(password)
        
        try:
            db.session.add(new_user)
            db.session.commit()
            current_app.logger.debug("User registered successfully")
        except Exception as e:
            current_app.logger.error(f"Error registering user: {e}")
            db.session.rollback()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'status': 'error',
                    'message': 'An error occurred during registration.'
                }), 500
            flash('An error occurred during registration.', 'danger')
            return redirect(url_for('auth.register_user'))
        
        # Log the registration
        log_entry = AuditLog(
            user_id=new_user.user_id,
            action="User registered"
        )
        db.session.add(log_entry)
        db.session.commit()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'status': 'success',
                'message': 'Registration successful! Please log in.',
                'redirect': url_for('auth.login_user')
            })
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login_user'))
    
    return render_template('register.html')

@auth_bp.route('/logout')
def logout_user():
    # Log the logout action if user is logged in
    if 'user_id' in session:
        log_entry = AuditLog(
            user_id=session['user_id'],
            action="User logged out"
        )
        db.session.add(log_entry)
        db.session.commit()
    
    # Clear the session
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login_user'))

@auth_bp.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        email = request.form.get('email')
        
        # Find the user
        user = User.query.filter_by(email=email).first()
        
        if user:
            # In a real app, we would send an email with a password reset link
            # For this simplified version, just show a message
            flash('Password reset instructions sent to your email.', 'info')
        else:
            flash('Email not found.', 'danger')
        
        return redirect(url_for('auth.login_user'))
    
    return render_template('reset.html')
