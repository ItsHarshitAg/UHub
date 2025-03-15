from flask import Blueprint, render_template, redirect, url_for, request, session, flash, jsonify
from app import db
from app.models.user import User
from app.models.audit import AuditLog
from app.models.notification import Notification
from app.models.friendship import FriendRequest
from app.utils.file_helpers import allowed_file, save_file
from werkzeug.utils import secure_filename
import os
from datetime import datetime

user_bp = Blueprint('user', __name__)

@user_bp.route('/user_dashboard')
def user_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('auth.login_user'))
    
    # Get current user
    current_user = User.query.get(session['user_id'])
    
    # Calculate actual counts
    skills_count = len(current_user.skills) if current_user.skills else 0
    projects_count = current_user.projects_count() if hasattr(current_user, 'projects_count') else len(current_user.projects)
    
    # Count friends (accepted friend requests)
    sent_accepted = FriendRequest.query.filter_by(sender_id=current_user.user_id, accepted=True).count()
    received_accepted = FriendRequest.query.filter_by(receiver_id=current_user.user_id, accepted=True).count()
    friends_count = sent_accepted + received_accepted
    
    # Get user-specific recent activities from audit logs
    recent_activities = AuditLog.query.filter_by(user_id=current_user.user_id)\
        .order_by(AuditLog.timestamp.desc())\
        .limit(5)\
        .all()
    
    # Format activities for display
    formatted_activities = []
    for activity in recent_activities:
        formatted_activities.append({
            'action': activity.action,
            'timestamp': activity.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        })
    
    # Log the successful access to the user dashboard
    new_log = AuditLog(
        user_id=session['user_id'],
        action=f'Accessed the user dashboard.'
    )
    db.session.add(new_log)
    db.session.commit()
    
    return render_template('user_dashboard.html', 
                          skills_count=skills_count,
                          projects_count=projects_count,
                          friends_count=friends_count,
                          activities=formatted_activities)  # Pass activities to template

@user_bp.route('/profile', methods=['GET', 'POST'])
def user_profile():
    if 'user_id' not in session:
        return redirect(url_for('auth.login_user'))

    user = User.query.get(session['user_id'])

    # Calculate actual statistics
    # Count friends (accepted friend requests)
    sent_accepted = FriendRequest.query.filter_by(sender_id=user.user_id, accepted=True).count()
    received_accepted = FriendRequest.query.filter_by(receiver_id=user.user_id, accepted=True).count()
    friends_count = sent_accepted + received_accepted
    
    # Get projects count
    projects_count = user.projects_count() if hasattr(user, 'projects_count') else len(user.projects)
    
    # For endorsements - currently doesn't exist in the model, so defaulting to 0
    # You can implement this feature if needed
    endorsements_count = 0

    if request.method == 'POST':
        # Update user's name and bio
        name = request.form['name']
        bio = request.form['bio']
        
        if not name:
            return redirect(url_for('user.user_profile'))

        user.name = name
        user.bio = bio

        # Handle profile picture upload
        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                upload_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'static', 'uploads')
                os.makedirs(upload_folder, exist_ok=True)
                file_path = os.path.join(upload_folder, filename)
                
                try:
                    # Save the file
                    file.save(file_path)

                    # Update the user's profile picture path in the database
                    user.profile_picture = filename
                except Exception as e:
                    return redirect(url_for('user.user_profile'))

        try:
            db.session.commit()
            # Log the profile update
            new_log = AuditLog(
                user_id=session['user_id'],
                action=f'Updated profile: Name: {name}, Bio: {bio}, Profile Picture: {user.profile_picture}.'
            )
            db.session.add(new_log)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
        
        return redirect(url_for('user.user_profile'))

    return render_template('profile.html', user=user, 
                          friends_count=friends_count,
                          projects_count=projects_count,
                          endorsements_count=endorsements_count)

@user_bp.route('/profile/<int:user_id>', methods=['GET'])
def view_profile(user_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login_user'))
    
    user = User.query.get_or_404(user_id)
    current_user = User.query.get(session['user_id'])
    
    # Determine friendship status
    friendship_status = 'not_friends'
    friend_request = FriendRequest.query.filter(
        ((FriendRequest.sender_id == current_user.user_id) & (FriendRequest.receiver_id == user.user_id)) |
        ((FriendRequest.sender_id == user.user_id) & (FriendRequest.receiver_id == current_user.user_id))
    ).first()
    
    if friend_request:
        if friend_request.accepted:
            friendship_status = 'friends'
        else:
            friendship_status = 'pending'
    
    return render_template('view_profile.html', user=user, current_user=current_user, friendship_status=friendship_status)

@user_bp.route('/search_users', methods=['GET'])
def search_users():
    if 'user_id' not in session:
        return redirect(url_for('auth.login_user'))

    query = request.args.get('query', '')
    if not query:
        return jsonify({"message": "No search query provided"}), 400

    users = User.query.filter(User.name.ilike(f'%{query}%')).all()
    if users:
        return jsonify([{"id": user.user_id, "name": user.name, "profile_picture": user.profile_picture} for user in users]), 200

    return jsonify({"message": "No users found"}), 404

@user_bp.route('/explore', methods=['GET'])
def explore():
    if 'user_id' not in session:
        return redirect(url_for('auth.login_user'))
    query = request.args.get('query', '')
    users = User.query.filter(User.name.ilike(f'%{query}%')).all()
    return render_template('explore.html', users=users, query=query)

@user_bp.route('/send_friend_request', methods=['POST'])
def send_friend_request():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please log in'}), 401

    data = request.get_json()
    sender_id = data.get('sender_id')
    receiver_id = data.get('receiver_id')

    # Validate sender_id matches logged-in user
    if sender_id != session['user_id']:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    # Check if an accepted friendship or pending request exists
    existing = FriendRequest.query.filter(
        ((FriendRequest.sender_id == sender_id) & (FriendRequest.receiver_id == receiver_id)) |
        ((FriendRequest.sender_id == receiver_id) & (FriendRequest.receiver_id == sender_id))
    ).first()

    if existing and existing.accepted:
        return jsonify({'success': False, 'message': 'You are already friends'})
    elif existing:
        return jsonify({'success': False, 'message': 'Friend request already sent'})

    # Create new friend request
    new_request = FriendRequest(sender_id=sender_id, receiver_id=receiver_id)
    db.session.add(new_request)

    # Fetch sender using SQLAlchemy 2.0-compatible method
    sender = db.session.get(User, sender_id)

    # Create notification for the receiver
    notification = Notification(
        receiver_id=receiver_id,
        sender_id=sender_id,
        type='friend_request',
        message=f"{sender.name} sent you a friend request."
    )
    db.session.add(notification)

    db.session.commit()

    return jsonify({'success': True, 'message': 'Friend request sent!'})

@user_bp.route('/unfriend', methods=['POST'])
def unfriend():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please log in'}), 401

    data = request.get_json()
    user_id = data.get('user_id')
    friend_id = data.get('friend_id')

    if not user_id or not friend_id:
        return jsonify({'success': False, 'message': 'Invalid request'}), 400

    # Validate user_id matches logged-in user
    if user_id != session['user_id']:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    friend_request = FriendRequest.query.filter(
        ((FriendRequest.sender_id == user_id) & (FriendRequest.receiver_id == friend_id) & FriendRequest.accepted) |
        ((FriendRequest.sender_id == friend_id) & (FriendRequest.receiver_id == user_id) & FriendRequest.accepted)
    ).first()

    if not friend_request:
        return jsonify({'success': False, 'message': 'No friendship exists'}), 404

    # Determine who is being notified (the other user)
    notified_user_id = friend_id
    unfriender = db.session.get(User, user_id)

    db.session.delete(friend_request)

    # Send notification to the unfriended user
    notification = Notification(
        recipient_id=notified_user_id,
        sender_id=user_id,
        type='unfriend',
        message=f"{unfriender.name} has unfriended you."
    )
    db.session.add(notification)

    # Log the action
    new_log = AuditLog(
        user_id=user_id,
        action=f"Unfriended user with ID {friend_id}"
    )
    db.session.add(new_log)

    db.session.commit()

    return jsonify({'success': True, 'message': 'User unfriended successfully'})

@user_bp.route('/accept_friend_request', methods=['POST'])
def accept_friend_request():
    if 'user_id' not in session:
        return redirect(url_for('auth.login_user'))
    
    data = request.get_json()
    notification_id = data.get('notification_id')
    
    notification = Notification.query.get(notification_id)
    if not notification or notification.receiver_id != session['user_id']:
        return jsonify({"message": "Invalid notification"}), 404
    
    friend_request = FriendRequest.query.filter_by(
        sender_id=notification.sender_id,
        receiver_id=notification.receiver_id
    ).first()
    
    if not friend_request:
        return jsonify({"message": "Friend request not found"}), 404
    
    friend_request.accepted = True
    
    # Create acceptance notification
    acceptance_notification = Notification(
        receiver_id=friend_request.sender_id,
        sender_id=friend_request.receiver_id,
        type="friend_request_acceptance",
        message=f"Your friend request to {User.query.get(friend_request.receiver_id).name} was accepted.",
        created_at=datetime.utcnow(),  # Use created_at instead of timestamp
        read=False  # Changed from is_read to read
    )
    
    db.session.add(acceptance_notification)
    db.session.delete(notification)  # Remove the original request notification
    db.session.commit()
    
    return jsonify({"message": "Friend request accepted"}), 200

@user_bp.route('/reject_friend_request', methods=['POST'])
def reject_friend_request():
    if 'user_id' not in session:
        return redirect(url_for('auth.login_user'))
    
    data = request.get_json()
    notification_id = data.get('notification_id')
    
    notification = Notification.query.get(notification_id)
    if not notification or notification.receiver_id != session['user_id']:
        return jsonify({"message": "Invalid notification"}), 404
    
    friend_request = FriendRequest.query.filter_by(
        sender_id=notification.sender_id,
        receiver_id=notification.receiver_id
    ).first()
    
    if friend_request:
        db.session.delete(friend_request)
    
    db.session.delete(notification)
    db.session.commit()
    
    return jsonify({"message": "Friend request rejected"}), 200

@user_bp.route('/get_notifications')
def get_notifications():
    """API endpoint to get user notifications."""
    if 'user_id' not in session:
        return jsonify([])
        
    user_id = session['user_id']
    
    # Get unread notifications for the current user
    notifications = Notification.query.filter_by(
        receiver_id=user_id, 
        read=False  # Changed from is_read to read to match the model
    ).order_by(Notification.created_at.desc()).all()  # Changed timestamp to created_at
    
    # Format notifications for JSON response
    notifications_list = []
    for notification in notifications:
        notification_data = {
            'id': notification.id,
            'sender_id': notification.sender_id,
            'type': notification.type,
            'message': notification.message,
            'timestamp': notification.created_at.strftime('%Y-%m-%d %H:%M:%S'),  # Use created_at instead of timestamp
            'is_read': notification.read  # Changed from is_read to read
        }
        notifications_list.append(notification_data)
    
    return jsonify(notifications_list)

@user_bp.route('/clear_notifications', methods=['POST'])
def clear_notifications():
    if 'user_id' not in session:
        return redirect(url_for('auth.login_user'))
    
    Notification.query.filter_by(recipient_id=session['user_id']).delete()
    db.session.commit()
    
    return jsonify({"message": "All notifications cleared"}), 200
