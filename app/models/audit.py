from app import db
from datetime import datetime

class AuditLog(db.Model):
    __tablename__ = 'audit'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    action = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Add explicit relationship to User
    user = db.relationship('User', backref=db.backref('audit_logs', lazy=True))
