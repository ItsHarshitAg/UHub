from app import db
from datetime import datetime

class ProjectChat(db.Model):
    __tablename__ = 'project_chat'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    
    # Timestamp field already defined
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Add standard timestamp fields for consistency
    created_at = db.Column(db.DateTime, nullable=True, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=True, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = db.relationship('Project', backref=db.backref('chat_messages', lazy=True))
    sender = db.relationship('User', backref=db.backref('project_messages', lazy=True))
