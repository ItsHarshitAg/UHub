# This file ensures the models directory is treated as a package
# All models should be imported in the application's __init__.py file

# Import all model classes to make them available for import from app.models
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
