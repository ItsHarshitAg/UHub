from app import db
from datetime import datetime

class Skill(db.Model):
    __tablename__ = 'skills'
    
    skill_id = db.Column(db.Integer, primary_key=True)
    skill_name = db.Column(db.String(100), nullable=False)
    proficiency = db.Column(db.Integer)  # 1-5 scale
    certificate_path = db.Column(db.String(255))
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Fix the relationship definition - change back_populates to match User.skills
    user = db.relationship("User", back_populates="skills")
    
    def __repr__(self):
        return f"<Skill {self.skill_name} ({self.proficiency}/5)>"
