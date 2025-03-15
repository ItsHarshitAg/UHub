from app import db
from datetime import datetime

class Message(db.Model):
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)
    
    # Fix relationship definitions to avoid conflicts with User model backref
    # Remove explicit relationship definitions since they're defined in the User model with backref
    # The relationships will be available through the backref defined in the User model
    
    def __repr__(self):
        return f"<Message {self.id}: from {self.sender_id} to {self.receiver_id}>"
