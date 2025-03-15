from app import create_app, db
from app.models.user import User
from app.models.skill import Skill
from app.models.project import Project, project_users
from app.models.task import Task
from app.models.message import Message
from app.models.notification import Notification
from app.models.friendship import FriendRequest
from app.models.audit import AuditLog
from app.models.project_chat import ProjectChat
from app.models.invitation import ProjectInvitation

def create_tables():
    """Create all database tables in one go"""
    app = create_app()
    with app.app_context():
        db.drop_all()  # Drop all existing tables
        db.create_all()  # Create all tables
        print("All tables created successfully!")

if __name__ == "__main__":
    create_tables()

