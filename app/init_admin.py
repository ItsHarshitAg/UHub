from app import db
from app.models.user import User
from datetime import datetime

def create_default_admin():
    """Create a default admin user if one doesn't exist."""
    # Check if admin exists
    admin = User.query.filter_by(email='admin@gmail.com').first()
    if not admin:
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
        print("Default admin user created.")
    else:
        print("Admin user already exists.")
