from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
import os
import sys
import logging
from urllib.parse import urlparse

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
bcrypt = Bcrypt()

def create_app(config_object=None):
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    
    # Configure the application
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key')
    
    # Configure database - handle PostgreSQL URL from Render
    database_url = os.environ.get('DATABASE_URL', 'sqlite:///../instance/database.db')
    # Fix potential "postgres://" to "postgresql://" for SQLAlchemy 1.4+
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'uploads')
    
    # Override with custom config if provided
    if config_object:
        app.config.from_object(config_object)
    
    # Ensure upload directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Set up logging
    app.logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    app.logger.addHandler(handler)
    
    # Wait for the database to be available if using PostgreSQL
    # This helps during deployment when the database might not be immediately ready
    try:
        from app.utils.database import wait_for_db
        wait_for_db(app)
    except Exception as e:
        app.logger.error(f"Database availability check failed: {str(e)}")
    
    # Initialize extensions with the app
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    
    # Import and register blueprints
    from app.routes.auth import auth_bp
    from app.routes.user import user_bp
    from app.routes.chat import chat_bp
    from app.routes.admin import admin_bp
    from app.routes.skills import skills_bp
    from app.routes.projects import projects_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(chat_bp, url_prefix='/chat')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(skills_bp, url_prefix='/skills')
    app.register_blueprint(projects_bp, url_prefix='/projects')
    
    # Create a route for the home page
    @app.route('/')
    def index():
        from flask import render_template
        return render_template('dashboard.html')
    
    # Context processor for user information
    @app.context_processor
    def inject_user():
        from flask import session
        from app.models.user import User
        if 'user_id' in session:
            current_user = User.query.get(session['user_id'])
            return {'current_user': current_user}
        return {'current_user': None}
    
    # Error handler for 500 errors
    @app.errorhandler(500)
    def internal_server_error(e):
        app.logger.error(f"500 error: {str(e)}")
        return jsonify({"status": "error", "message": "Server error. Please try again later."}), 500
    
    # Import models to ensure they're registered with SQLAlchemy
    with app.app_context():
        try:
            from app.models.user import User
            from app.models.message import Message
            from app.models.notification import Notification
            from app.models.friendship import FriendRequest
            from app.models.skill import Skill
            from app.models.audit import AuditLog
            from app.models.project import Project
            from app.models.task import Task
            from app.models.project_chat import ProjectChat
            from app.models.invitation import ProjectInvitation
            
            # Create all tables if they don't exist
            db.create_all()
            
            # Run migrations if migration table exists (meaning Flask-Migrate has been initialized)
            try:
                from flask_migrate import upgrade
                from sqlalchemy.exc import ProgrammingError
                
                # Check if alembic_version table exists (indicating migrations are set up)
                try:
                    db.session.execute(db.text("SELECT * FROM alembic_version"))
                    # If the query succeeds, run migrations
                    app.logger.info("Running database migrations...")
                    upgrade()
                    app.logger.info("Database migrations completed successfully.")
                except ProgrammingError:
                    # If alembic_version doesn't exist, initialize migrations
                    app.logger.info("Initializing Flask-Migrate...")
                    from flask_migrate import init, migrate, stamp
                    init()
                    migrate()
                    stamp()
                    app.logger.info("Flask-Migrate initialized.")
            except Exception as e:
                app.logger.error(f"Error during migration: {str(e)}")
                
            # Initialize default admin user
            from app.init_admin import create_default_admin
            create_default_admin()
        except Exception as e:
            app.logger.error(f"Error during startup: {str(e)}")
            import traceback
            app.logger.error(traceback.format_exc())
    
    return app
