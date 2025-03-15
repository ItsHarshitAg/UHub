from app import db, bcrypt
from datetime import datetime
from sqlalchemy.orm import relationship

class User(db.Model):
    __tablename__ = 'users'
    
    user_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(100), nullable=False)  # Hashed password
    role = db.Column(db.String(50), nullable=False)
    bio = db.Column(db.Text, nullable=True)
    profile_picture = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    
    # Relationships with consistent naming
    skills = relationship("Skill", back_populates="user", cascade="all, delete-orphan")
    projects = relationship("Project", secondary="project_users", back_populates="users")
    created_projects = relationship("Project", foreign_keys="Project.created_by", back_populates="creator")
    
    # Messages
    sent_messages = relationship("Message", foreign_keys="Message.sender_id", backref="sender")
    received_messages = relationship("Message", foreign_keys="Message.receiver_id", backref="receiver")
    
    # Friend requests
    sent_requests = relationship("FriendRequest", foreign_keys="FriendRequest.sender_id", backref="sender_user")
    received_requests = relationship("FriendRequest", foreign_keys="FriendRequest.receiver_id", backref="receiver_user")
    
    # Notifications
    notifications_received = relationship("Notification", foreign_keys="Notification.receiver_id", backref="receiver")
    notifications_sent = relationship("Notification", foreign_keys="Notification.sender_id", backref="sender")
    
    def __repr__(self):
        return f"<User {self.name}>"
        
    def projects_count(self):
        """Return the count of projects the user is part of"""
        return len(self.projects) + len(self.created_projects)
    
    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)
