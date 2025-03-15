from app import db
from datetime import datetime

class FriendRequest(db.Model):
    __tablename__ = 'friend_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, accepted, declined
    accepted = db.Column(db.Boolean, default=False)  # Add this field to match your queries
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Fix relationship definitions to avoid conflicts with User model backref
    # Remove explicit relationship definitions since they're defined in the User model with backref
    # The relationships will be available through the backref defined in the User model
    
    def __repr__(self):
        return f"<FriendRequest {self.id}: from {self.sender_id} to {self.receiver_id}>"
