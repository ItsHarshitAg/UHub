from app import db
from datetime import datetime
from sqlalchemy.orm import relationship

class Task(db.Model):
    __tablename__ = 'tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    assignee_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=True)
    creator_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    
    # Kanban status: todo, in_progress, review, completed
    status = db.Column(db.String(50), default='todo')
    
    # Task priority: low, medium, high, urgent
    priority = db.Column(db.String(20), default='medium')
    
    # Position in Kanban column (for ordering)
    position = db.Column(db.Integer, default=0)
    
    due_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = relationship('Project', back_populates='tasks')
    assignee = relationship('User', foreign_keys=[assignee_id], backref='assigned_tasks')
    creator = relationship('User', foreign_keys=[creator_id], backref='created_tasks')
    
    def __repr__(self):
        return f"<Task {self.name}>"
