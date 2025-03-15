from app import db
from datetime import datetime

# Association table for many-to-many relationship between projects and users
project_users = db.Table('project_users',
    db.Column('project_id', db.Integer, db.ForeignKey('projects.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('users.user_id'), primary_key=True)
)

class Project(db.Model):
    __tablename__ = 'projects'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    required_skills = db.Column(db.Text, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Ensure consistent relationship naming
    users = db.relationship('User', secondary=project_users, back_populates='projects')
    creator = db.relationship('User', foreign_keys=[created_by], back_populates='created_projects')
    tasks = db.relationship('Task', back_populates='project', cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Project {self.name}>"

class ProjectUser(db.Model):
    __tablename__ = 'project_user'

    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), primary_key=True)
