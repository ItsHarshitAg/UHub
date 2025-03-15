from flask import Blueprint, render_template, redirect, url_for, request, session, flash, jsonify
from app import db
from app.models.user import User
from app.models.message import Message
from app.models.audit import AuditLog
from app.models.friendship import FriendRequest
from datetime import datetime

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/')
def index():
    return redirect(url_for('auth.login_user'))  # Change to redirect instead of rendering template

@chat_bp.route('/chat/<int:friend_id>', methods=['GET'])
def chat(friend_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login_user'))

    current_user = User.query.get(session['user_id'])
    friend = User.query.get_or_404(friend_id)

    # Check if they are friends
    friend_request = FriendRequest.query.filter(
        ((FriendRequest.sender_id == current_user.user_id) & (FriendRequest.receiver_id == friend.user_id) & FriendRequest.accepted) |
        ((FriendRequest.sender_id == friend.user_id) & (FriendRequest.receiver_id == current_user.user_id) & FriendRequest.accepted)
    ).first()

    if not friend_request:
        flash('You can only chat with friends.', 'danger')
        return redirect(url_for('user.explore'))

    # Fetch chat history
    messages = Message.query.filter(
        ((Message.sender_id == current_user.user_id) & (Message.receiver_id == friend.user_id)) |
        ((Message.sender_id == friend.user_id) & (Message.receiver_id == current_user.user_id))
    ).order_by(Message.timestamp.asc()).all()

    return render_template('chat.html', friend=friend, messages=messages, current_user=current_user)

@chat_bp.route('/send_message', methods=['POST'])
def send_message():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please log in'}), 401

    data = request.get_json()
    receiver_id = data.get('receiver_id')
    content = data.get('content')

    if not receiver_id or not content:
        return jsonify({'success': False, 'message': 'Receiver ID and message content are required'}), 400

    sender_id = session['user_id']
    friend = User.query.get(receiver_id)

    # Check if they are friends
    friend_request = FriendRequest.query.filter(
        ((FriendRequest.sender_id == sender_id) & (FriendRequest.receiver_id == receiver_id) & FriendRequest.accepted) |
        ((FriendRequest.sender_id == receiver_id) & (FriendRequest.receiver_id == sender_id) & FriendRequest.accepted)
    ).first()

    if not friend_request:
        return jsonify({'success': False, 'message': 'You can only chat with friends'}), 403

    # Create and save the message
    new_message = Message(
        sender_id=sender_id,
        receiver_id=receiver_id,
        content=content
    )
    db.session.add(new_message)
    db.session.commit()

    # Log the message sending action
    new_log = AuditLog(
        user_id=sender_id,
        action=f'Sent a message to user ID {receiver_id}'
    )
    db.session.add(new_log)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Message sent successfully',
        'data': {
            'id': new_message.id,
            'content': new_message.content,
            'timestamp': new_message.timestamp.isoformat(),
            'sender_id': new_message.sender_id
        }
    })

@chat_bp.route('/get_messages/<int:friend_id>', methods=['GET'])
def get_messages(friend_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please log in'}), 401

    current_user_id = session['user_id']
    friend = User.query.get_or_404(friend_id)

    # Check if they are friends
    friend_request = FriendRequest.query.filter(
        ((FriendRequest.sender_id == current_user_id) & (FriendRequest.receiver_id == friend.user_id) & FriendRequest.accepted) |
        ((FriendRequest.sender_id == friend.user_id) & (FriendRequest.receiver_id == current_user_id) & FriendRequest.accepted)
    ).first()

    if not friend_request:
        return jsonify({'success': False, 'message': 'You can only view messages with friends'}), 403

    # Fetch messages
    messages = Message.query.filter(
        ((Message.sender_id == current_user_id) & (Message.receiver_id == friend_id)) |
        ((Message.sender_id == friend_id) & (Message.receiver_id == current_user_id))
    ).order_by(Message.timestamp.asc()).all()

    messages_data = [{
        'id': msg.id,
        'sender_id': msg.sender_id,
        'receiver_id': msg.receiver_id,
        'content': msg.content,
        'timestamp': msg.timestamp.isoformat(),
        'is_read': msg.is_read
    } for msg in messages]

    # Mark unread messages as read
    for msg in messages:
        if msg.receiver_id == current_user_id and not msg.is_read:
            msg.is_read = True
    db.session.commit()

    return jsonify({'success': True, 'messages': messages_data})

@chat_bp.route('/chat_list')
def chat_list():
    if 'user_id' not in session:
        return redirect(url_for('auth.login_user'))

    current_user = User.query.get(session['user_id'])

    # Get all accepted friend requests where the current user is either sender or receiver
    friend_requests = FriendRequest.query.filter(
        FriendRequest.accepted == True,
        (FriendRequest.sender_id == current_user.user_id) | (FriendRequest.receiver_id == current_user.user_id)
    ).all()

    # Extract friend IDs and fetch User objects
    friend_ids = [
        fr.receiver_id if fr.sender_id == current_user.user_id else fr.sender_id
        for fr in friend_requests
    ]
    friends = User.query.filter(User.user_id.in_(friend_ids)).all()

    return render_template('chat_list.html', friends=friends)
