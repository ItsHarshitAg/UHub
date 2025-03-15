from app import db
from app.models.user import User
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def create_default_admin():
    """Create a default admin user if one doesn't exist."""
    try:
        # Check if admin exists
        admin = User.query.filter_by(email='admin@gmail.com').first()
        if not admin:
            logger.info("Creating default admin user...")
            # Create admin user
            admin = User(
                name='Administrator',
                email='admin@gmail.com',
                role='admin',
                bio='System administrator',
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            admin.set_password('admin')
            db.session.add(admin)
            db.session.commit()
            logger.info("Default admin user created successfully.")
            return True, "Default admin user created successfully."
        else:
            logger.info("Admin user already exists.")
            return True, "Admin user already exists."
    except Exception as e:
        logger.error(f"Error creating default admin user: {str(e)}")
        db.session.rollback()
        return False, f"Error creating default admin user: {str(e)}"
