from flask import Blueprint, render_template, redirect, url_for, request, session, flash, jsonify
from app import db
from app.models.skill import Skill
from app.models.user import User
from app.models.project import Project
from app.models.audit import AuditLog
from app.models.task import Task  # Import the Task model
from app.models.project_chat import ProjectChat  # Import the ProjectChat model
from app.models.invitation import ProjectInvitation  # Import the ProjectInvitation model
from datetime import datetime

projects_bp = Blueprint('projects', __name__)

@projects_bp.route('/manage_projects', methods=['GET', 'POST'])
def manage_projects():
    if 'user_id' not in session:
        return redirect(url_for('auth.login_user'))

    user = User.query.get(session['user_id'])
    
    # Get all projects with eager loading of relationships
    projects = Project.query.options(
        db.joinedload(Project.users),
        db.joinedload(Project.creator)
    ).all()

    # Create a dictionary to check if the user is a member of each project
    user_projects = {}
    for project in projects:
        user_projects[project.id] = user in project.users or project.created_by == user.user_id

    if request.method == 'POST':
        # Check if request is JSON (from AJAX) or form data
        if request.is_json:
            data = request.get_json()
            project_name = data.get('project_name')
            project_description = data.get('project_description')
            required_skills = data.get('required_skills_string')
        else:
            project_name = request.form.get('project_name')
            project_description = request.form.get('project_description')
            
            # Get skills either from the select2 multiple select or from the hidden field
            if 'required_skills_string' in request.form:
                required_skills = request.form.get('required_skills_string')
            else:
                # For backward compatibility or if using normal select
                skills_list = request.form.getlist('required_skills')
                required_skills = ', '.join(skills_list)
        
        # Validate required fields
        if not project_name or not project_description or not required_skills:
            if request.is_json:
                return jsonify({
                    'success': False,
                    'message': 'All fields are required'
                }), 400
            else:
                flash('All fields are required', 'danger')
                return redirect(url_for('projects.manage_projects'))
        
        # Create new project
        new_project = Project(
            name=project_name,
            description=project_description,
            required_skills=required_skills,
            created_by=user.user_id
        )
        
        db.session.add(new_project)
        
        # Add creator to project members
        new_project.users.append(user)
        
        # Log the project creation
        new_log = AuditLog(
            user_id=user.user_id,
            action=f'Created project: {project_name}'
        )
        db.session.add(new_log)
        db.session.commit()

        # Return appropriate response based on request type
        if request.is_json:
            return jsonify({
                'success': True, 
                'message': 'Project created successfully',
                'project_id': new_project.id
            })
        else:
            flash('Project created successfully!', 'success')
            return redirect(url_for('projects.manage_projects'))

    # Get user skills for skill filter dropdown
    user_skills = [skill.skill_name for skill in user.skills] if user.skills else []
    
    # Get statistics for dashboard
    stats = {
        'total_projects': len(projects),
        'my_projects': sum(1 for p in projects if p.created_by == user.user_id),
        'joined_projects': sum(1 for p in projects if user in p.users and p.created_by != user.user_id)
    }

    return render_template('projects.html', 
                           projects=projects, 
                           user_projects=user_projects,
                           user_skills=user_skills,
                           stats=stats)

def join_project_CR(project_id, c_id):
    """Helper function to join a user to a project"""
    project = Project.query.get_or_404(project_id)
    user = User.query.get(c_id)

    if user not in project.users:
        project.users.append(user)
        db.session.commit()

        # Log the join action
        new_log = AuditLog(
            user_id=c_id,
            action=f'User joined project (ID: {project_id}).'
        )
        db.session.add(new_log)
        db.session.commit()

@projects_bp.route('/edit_project/<int:project_id>', methods=['GET', 'POST'])
def edit_project(project_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login_user'))

    project = Project.query.get_or_404(project_id)
    all_skills = Skill.query.order_by(Skill.skill_name).all()

    # Check if the logged-in user is the creator of the project
    if project.created_by != session['user_id']:
        flash('You do not have permission to edit this project.', 'danger')
        return redirect(url_for('projects.project_dashboard', project_id=project_id))

    # Get project tasks and team members for the advanced edit page
    tasks = Task.query.filter_by(project_id=project_id).all()
    team_members = User.query.join(
        Project.users
    ).filter(Project.id == project_id, User.user_id != project.created_by).all()

    if request.method == 'POST':
        project.name = request.form.get('project_name')
        project.description = request.form.get('project_description')
        
        # Get skills either from the select2 multiple select or from the hidden field
        if 'required_skills_string' in request.form:
            project.required_skills = request.form.get('required_skills_string')
        else:
            # For backward compatibility or if using normal select
            skills_list = request.form.getlist('required_skills')
            project.required_skills = ', '.join(skills_list)
        
        db.session.commit()
        
        # Log the project edit
        new_log = AuditLog(
            user_id=session['user_id'],
            action=f'Updated project: {project.name}'
        )
        db.session.add(new_log)
        db.session.commit()
        
        flash('Project updated successfully!', 'success')
        return redirect(url_for('projects.project_dashboard', project_id=project_id))

    return render_template('edit_project.html', 
                          project=project,
                          tasks=tasks,
                          team_members=team_members,
                          all_skills=all_skills)

@projects_bp.route('/delete_project/<int:project_id>', methods=['GET', 'POST'])
def delete_project(project_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login_user'))

    project = Project.query.get_or_404(project_id)

    # Check if the logged-in user is the creator of the project or an admin
    if project.created_by != session['user_id'] and session.get('role') != 'admin':
        # Log unauthorized attempt to delete project
        new_log = AuditLog(
            user_id=session['user_id'],
            action=f'Attempted to delete a project they do not own (Project ID: {project_id}).'
        )
        db.session.add(new_log)
        db.session.commit()

        return redirect(url_for('projects.manage_projects'))

    db.session.delete(project)
    db.session.commit()

    # Log the project deletion
    new_log = AuditLog(
        user_id=session['user_id'],
        action=f'Deleted project (ID: {project_id}).'
    )
    db.session.add(new_log)
    db.session.commit()

    return redirect(url_for('projects.manage_projects'))

@projects_bp.route('/quit_project/<int:project_id>', methods=['POST'])
def quit_project(project_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login_user'))

    project = Project.query.get_or_404(project_id)
    user = User.query.get(session['user_id'])

    # Check if the user is already a member of the project
    if user in project.users:
        project.users.remove(user)
        db.session.commit()

        # Log the quit action
        new_log = AuditLog(
            user_id=user.user_id,
            action=f'User quit project (ID: {project_id}).'
        )
        db.session.add(new_log)
        db.session.commit()

    return redirect(url_for('projects.manage_projects'))

@projects_bp.route('/join_project/<int:project_id>', methods=['POST'])
def join_project(project_id):
    if 'user_id' not in session:
        flash('Please log in to join a project.', 'danger')
        return redirect(url_for('auth.login_user'))

    project = Project.query.get_or_404(project_id)
    user = User.query.get(session['user_id'])

    # Check if the user is already part of the project
    if user not in project.users:
        project.users.append(user)
        db.session.commit()

        # Log the join action
        new_log = AuditLog(
            user_id=user.user_id,
            action=f'User joined project (ID: {project_id}).'
        )
        db.session.add(new_log)
        db.session.commit()

        flash('You have successfully joined the project!', 'success')
    else:
        flash('You are already a member of this project.', 'danger')

    return redirect(url_for('projects.manage_projects'))

@projects_bp.route('/get_project_members/<int:project_id>')
def get_project_members(project_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login_user'))

    project = Project.query.get_or_404(project_id)
    
    # Get the list of project members
    members = project.users[:]
    creator = User.query.get(project.created_by)
    if creator not in members:
        members.append(creator)
    
    # Format the members as a list of dictionaries
    members_data = [{'id': user.user_id, 'name': user.name} for user in members]

    # Return the members as JSON
    return jsonify(members_data)

@projects_bp.route('/remove_member/<int:project_id>/<int:member_id>', methods=['POST'])
def remove_member(project_id, member_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login_user'))

    project = Project.query.get_or_404(project_id)
    user = User.query.get(member_id)

    # Check if the logged-in user is the project creator
    if project.created_by == session['user_id']:
        if user in project.users:
            project.users.remove(user)
            db.session.commit()

            # Log the removal action
            new_log = AuditLog(
                user_id=session['user_id'],
                action=f'Removed user {user.name} from project (ID: {project_id}).'
            )
            db.session.add(new_log)
            db.session.commit()

            return '', 204  # Return a successful response with no content

    return '', 400  # Return an error if not authorized to remove members

@projects_bp.route('/project_dashboard/<int:project_id>')
def project_dashboard(project_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login_user'))
    
    project = Project.query.get_or_404(project_id)
    current_user = User.query.get(session['user_id'])
    
    # Check if user is a member of the project
    is_member = current_user in project.users or project.created_by == current_user.user_id
    if not is_member:
        flash('You do not have access to this project', 'danger')
        return redirect(url_for('projects.manage_projects'))
    
    # Get tasks
    tasks = Task.query.filter_by(project_id=project_id).all()
    
    # Get team members
    team_members = list(project.users)
    creator = User.query.get(project.created_by)
    if creator not in team_members:
        team_members.append(creator)
    
    # Count tasks by status
    completed_tasks = Task.query.filter_by(project_id=project_id, status='completed').count()
    pending_tasks = len(tasks) - completed_tasks
    
    # Calculate progress
    progress = int((completed_tasks / max(len(tasks), 1)) * 100)
    
    # Log the dashboard access
    new_log = AuditLog(
        user_id=current_user.user_id,
        action=f'Accessed dashboard for project: {project.name}'
    )
    db.session.add(new_log)
    db.session.commit()
    
    return render_template(
        'project_dashboard.html',
        project=project,
        current_user=current_user,
        tasks=tasks,
        team_members=team_members,
        completed_tasks=completed_tasks,
        pending_tasks=pending_tasks,
        progress=progress
    )

# Task Management Routes
@projects_bp.route('/create_task/<int:project_id>', methods=['POST'])
def create_task(project_id):
    if 'user_id' not in session:
        if request.content_type == 'application/json':
            return jsonify({'success': False, 'message': 'Please log in'}), 401
        flash('Please log in to continue', 'danger')
        return redirect(url_for('auth.login_user'))
    
    current_user_id = session['user_id']
    project = Project.query.get_or_404(project_id)
    
    # Check if user is authorized to add tasks
    is_member = current_user_id == project.created_by or User.query.get(current_user_id) in project.users
    if not is_member:
        if request.content_type == 'application/json':
            return jsonify({'success': False, 'message': 'You are not authorized to manage tasks in this project'}), 403
        flash('You are not authorized to manage tasks in this project', 'danger')
        return redirect(url_for('projects.project_dashboard', project_id=project_id))
    
    try:
        # Get task data from request - handle both JSON and form data
        if request.content_type == 'application/json':
            data = request.get_json()
        else:
            data = request.form
            
        print(f"Received task data: {data}")  # Debug log
        
        name = data.get('name')
        description = data.get('description', '')
        assignee_id = data.get('assignee_id')
        status = data.get('status', 'todo')
        priority = data.get('priority', 'medium')
        due_date_str = data.get('due_date')
        
        # Validate required fields
        if not name:
            if request.content_type == 'application/json':
                return jsonify({'success': False, 'message': 'Task name is required'}), 400
            flash('Task name is required', 'danger')
            return redirect(url_for('projects.add_task', project_id=project_id))
        
        # Parse due date if provided
        due_date = None
        if due_date_str:
            try:
                due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
            except ValueError:
                if request.content_type == 'application/json':
                    return jsonify({'success': False, 'message': 'Invalid due date format'}), 400
                flash('Invalid due date format', 'danger')
                return redirect(url_for('projects.add_task', project_id=project_id))
        
        # Create and save the task
        new_task = Task(
            name=name,
            description=description,
            project_id=project_id,
            assignee_id=assignee_id if assignee_id else None,
            creator_id=current_user_id,
            status=status,
            priority=priority,
            due_date=due_date
        )
        
        db.session.add(new_task)
        db.session.flush()  # Get the ID without committing
        
        task_id = new_task.id
        
        # Log the task creation
        new_log = AuditLog(
            user_id=current_user_id,
            action=f'Created task "{name}" in project: {project.name}'
        )
        db.session.add(new_log)
        db.session.commit()
        
        print(f"Task created successfully: ID={new_task.id}")  # Debug log
        
        # Handle JSON response vs form response
        if request.content_type == 'application/json':
            return jsonify({
                'success': True,
                'message': 'Task created successfully',
                'task': {
                    'id': new_task.id,
                    'name': new_task.name,
                    'description': new_task.description,
                    'status': new_task.status,
                    'priority': new_task.priority,
                    'due_date': new_task.due_date.strftime('%Y-%m-%d') if new_task.due_date else None
                }
            })
        else:
            flash('Task created successfully!', 'success')
            return redirect(url_for('projects.project_dashboard', project_id=project_id))
            
    except Exception as e:
        db.session.rollback()
        print(f"Error creating task: {str(e)}")
        if request.content_type == 'application/json':
            return jsonify({'success': False, 'message': f'Error creating task: {str(e)}'}), 500
        flash(f'Error creating task: {str(e)}', 'danger')
        return redirect(url_for('projects.add_task', project_id=project_id))

# Add this new route for traditional form submission

@projects_bp.route('/create_task_form/<int:project_id>', methods=['POST'])
def create_task_form(project_id):
    """Handle traditional form submission for task creation"""
    if 'user_id' not in session:
        flash('Please log in to continue', 'danger')
        return redirect(url_for('auth.login_user'))
    
    current_user_id = session['user_id']
    project = Project.query.get_or_404(project_id)
    
    # Check if user is authorized to add tasks
    is_member = current_user_id == project.created_by or User.query.get(current_user_id) in project.users
    if not is_member:
        flash('You are not authorized to manage tasks in this project', 'danger')
        return redirect(url_for('projects.project_dashboard', project_id=project_id))
    
    try:
        # Get form data
        name = request.form.get('name')
        description = request.form.get('description', '')
        assignee_id = request.form.get('assignee_id')
        status = request.form.get('status', 'todo')
        priority = request.form.get('priority', 'medium')
        due_date_str = request.form.get('due_date')
        
        # Validate required fields
        if not name:
            flash('Task name is required', 'danger')
            return redirect(url_for('projects.add_task', project_id=project_id))
        
        # Parse due date if provided
        due_date = None
        if due_date_str:
            try:
                due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
            except ValueError:
                flash('Invalid due date format', 'danger')
                return redirect(url_for('projects.add_task', project_id=project_id))
        
        # Create and save the task
        new_task = Task(
            name=name,
            description=description,
            project_id=project_id,
            assignee_id=assignee_id if assignee_id else None,
            creator_id=current_user_id,
            status=status,
            priority=priority,
            due_date=due_date
        )
        
        db.session.add(new_task)
        
        # Log the task creation
        new_log = AuditLog(
            user_id=current_user_id,
            action=f'Created task "{name}" in project: {project.name}'
        )
        db.session.add(new_log)
        db.session.commit()
        
        flash('Task created successfully!', 'success')
        return redirect(url_for('projects.project_dashboard', project_id=project_id))
            
    except Exception as e:
        db.session.rollback()
        flash(f'Error creating task: {str(e)}', 'danger')
        return redirect(url_for('projects.add_task', project_id=project_id))

@projects_bp.route('/update_task/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please log in'}), 401
    
    current_user_id = session['user_id']
    task = Task.query.get_or_404(task_id)
    project = Project.query.get(task.project_id)
    
    # Check authorization
    is_authorized = (current_user_id == project.created_by or 
                     current_user_id == task.assignee_id or 
                     current_user_id == task.creator_id)
    if not is_authorized:
        return jsonify({'success': False, 'message': 'You are not authorized to update this task'}), 403
    
    # Get update data
    data = request.get_json()
    
    # Update task fields if provided
    if 'name' in data:
        task.name = data['name']
    if 'description' in data:
        task.description = data['description']
    if 'assignee_id' in data:
        task.assignee_id = data['assignee_id']
    if 'status' in data:
        task.status = data['status']
    if 'priority' in data:
        task.priority = data['priority']
    if 'due_date' in data and data['due_date']:
        try:
            task.due_date = datetime.strptime(data['due_date'], '%Y-%m-%d')
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid due date format'}), 400
    
    # Log the task update
    new_log = AuditLog(
        user_id=current_user_id,
        action=f'Updated task "{task.name}" in project: {project.name}'
    )
    db.session.add(new_log)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Task updated successfully'})

@projects_bp.route('/delete_task/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please log in'}), 401
    
    current_user_id = session['user_id']
    task = Task.query.get_or_404(task_id)
    project = Project.query.get(task.project_id)
    
    # Check if user is authorized (project creator or task creator)
    is_authorized = current_user_id == project.created_by or current_user_id == task.creator_id
    if not is_authorized:
        return jsonify({'success': False, 'message': 'You are not authorized to delete this task'}), 403
    
    task_name = task.name
    project_name = project.name
    
    db.session.delete(task)
    
    # Log the task deletion
    new_log = AuditLog(
        user_id=current_user_id,
        action=f'Deleted task "{task_name}" from project: {project_name}'
    )
    db.session.add(new_log)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Task deleted successfully'})

@projects_bp.route('/get_project_tasks/<int:project_id>')
def get_project_tasks(project_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please log in'}), 401
    
    current_user_id = session['user_id']
    project = Project.query.get_or_404(project_id)
    
    # Check if user is a member of the project
    is_member = current_user_id == project.created_by or User.query.get(current_user_id) in project.users
    if not is_member:
        return jsonify({'success': False, 'message': 'You do not have access to this project'}), 403
    
    # Get tasks
    tasks = Task.query.filter_by(project_id=project_id).all()
    
    # Format tasks as dictionaries
    tasks_data = []
    for task in tasks:
        assignee = User.query.get(task.assignee_id) if task.assignee_id else None
        tasks_data.append({
            'id': task.id,
            'name': task.name,
            'description': task.description,
            'status': task.status,
            'priority': task.priority,
            'due_date': task.due_date.strftime('%Y-%m-%d') if task.due_date else None,
            'assignee': assignee.name if assignee else None,
            'assignee_id': task.assignee_id
        })
    
    return jsonify({'success': True, 'tasks': tasks_data})

# Project Chat Routes
@projects_bp.route('/send_project_message/<int:project_id>', methods=['POST'])
def send_project_message(project_id):
    """Send a message in the project chat"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please log in'}), 401
    
    current_user_id = session['user_id']
    project = Project.query.get_or_404(project_id)
    
    # Check if user is a member of the project
    is_member = current_user_id == project.created_by or User.query.get(current_user_id) in project.users
    if not is_member:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    # Get message content
    data = request.json
    content = data.get('content')
    
    if not content or not content.strip():
        return jsonify({'success': False, 'message': 'Message cannot be empty'}), 400
    
    # Create and save the message
    new_message = ProjectChat(
        project_id=project_id,
        sender_id=current_user_id,
        content=content
    )
    
    db.session.add(new_message)
    db.session.commit()
    
    # Format response
    sender = User.query.get(current_user_id)
    
    return jsonify({
        'success': True,
        'message': {
            'id': new_message.id,
            'content': new_message.content,
            'sender_id': new_message.sender_id,
            'sender_name': sender.name,
            'timestamp': new_message.timestamp.isoformat()
        }
    })

@projects_bp.route('/get_project_messages/<int:project_id>')
def get_project_messages(project_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please log in'}), 401
    
    current_user_id = session['user_id']
    project = Project.query.get_or_404(project_id)
    
    # Check if user is a member of the project
    is_member = current_user_id == project.created_by or User.query.get(current_user_id) in project.users
    if not is_member:
        return jsonify({'success': False, 'message': 'You do not have access to this project'}), 403
    
    # Get messages
    messages = ProjectChat.query.filter_by(project_id=project_id).order_by(ProjectChat.timestamp.asc()).all()
    
    # Format messages as dictionaries
    messages_data = []
    for msg in messages:
        sender = User.query.get(msg.sender_id)
        messages_data.append({
            'id': msg.id,
            'content': msg.content,
            'sender_id': msg.sender_id,
            'sender_name': sender.name if sender else 'Unknown User',
            'timestamp': msg.timestamp.isoformat()
        })
    
    return jsonify({'success': True, 'messages': messages_data})

# Team Management Routes
@projects_bp.route('/invite_to_project/<int:project_id>', methods=['POST'])
def invite_to_project(project_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please log in'}), 401
    
    current_user_id = session['user_id']
    project = Project.query.get_or_404(project_id)
    
    # Check if user is authorized to invite (project creator or admin)
    is_authorized = current_user_id == project.created_by or session.get('role') == 'admin'
    if not is_authorized:
        return jsonify({'success': False, 'message': 'You are not authorized to invite users to this project'}), 403
    
    # Get invitation data
    data = request.get_json()
    recipient_ids = data.get('recipient_ids', [])
    message = data.get('message', '')
    
    if not recipient_ids:
        return jsonify({'success': False, 'message': 'No recipients selected'}), 400
    
    # Process invitations
    invitations_sent = 0
    for recipient_id in recipient_ids:
        # Check if recipient exists
        recipient = User.query.get(recipient_id)
        if not recipient:
            continue
        
        # Check if recipient is already a member
        if recipient in project.users or recipient_id == project.created_by:
            continue
        
        # Check if invitation already exists
        existing_invitation = ProjectInvitation.query.filter_by(
            project_id=project_id,
            recipient_id=recipient_id,
            status='pending'
        ).first()
        
        if existing_invitation:
            continue
        
        # Create and save the invitation
        new_invitation = ProjectInvitation(
            project_id=project_id,
            sender_id=current_user_id,
            recipient_id=recipient_id,
            message=message
        )
        
        db.session.add(new_invitation)
        invitations_sent += 1
    
    if invitations_sent > 0:
        # Log the invitation action
        new_log = AuditLog(
            user_id=current_user_id,
            action=f'Invited {invitations_sent} users to project: {project.name}'
        )
        db.session.add(new_log)
        db.session.commit()
        
        return jsonify({'success': True, 'message': f'Sent {invitations_sent} invitations successfully'})
    else:
        return jsonify({'success': False, 'message': 'No new invitations were sent'}), 400

@projects_bp.route('/get_users_by_skill')
def get_users_by_skill():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please log in'}), 401
    
    skill_name = request.args.get('skill', '')
    project_id = request.args.get('project_id')
    
    if not project_id:
        return jsonify({'success': False, 'message': 'Project ID is required'}), 400
    
    # Get project
    project = Project.query.get_or_404(project_id)
    
    # Get users with matching skill
    users_query = User.query
    
    if skill_name:
        # Find users with the specific skill
        users_query = users_query.join(User.skills).filter(db.func.lower(Skill.skill_name) == db.func.lower(skill_name))
    
    # Exclude users already in the project
    users = users_query.filter(
        User.user_id != project.created_by,  # Exclude creator
        ~User.user_id.in_([user.user_id for user in project.users])  # Exclude members
    ).all()
    
    # Format users as dictionaries
    users_data = []
    for user in users:
        user_skills = [skill.skill_name for skill in user.skills]
        users_data.append({
            'id': user.user_id,
            'name': user.name,
            'email': user.email,
            'skills': user_skills
        })
    
    return jsonify({'success': True, 'users': users_data})

@projects_bp.route('/accept_project_invitation/<int:invitation_id>', methods=['POST'])
def accept_project_invitation(invitation_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please log in'}), 401
    
    current_user_id = session['user_id']
    invitation = ProjectInvitation.query.get_or_404(invitation_id)
    
    # Check if the invitation is for the current user
    if invitation.recipient_id != current_user_id:
        return jsonify({'success': False, 'message': 'You are not authorized to respond to this invitation'}), 403
    
    # Check if the invitation is pending
    if invitation.status != 'pending':
        return jsonify({'success': False, 'message': 'This invitation has already been processed'}), 400
    
    project = Project.query.get(invitation.project_id)
    if not project:
        return jsonify({'success': False, 'message': 'The project no longer exists'}), 400
    
    # Accept the invitation
    invitation.status = 'accepted'
    
    # Add user to project
    user = User.query.get(current_user_id)
    project.users.append(user)
    
    # Log the acceptance
    new_log = AuditLog(
        user_id=current_user_id,
        action=f'Accepted invitation to join project: {project.name}'
    )
    db.session.add(new_log)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'You have joined the project successfully'})

@projects_bp.route('/decline_project_invitation/<int:invitation_id>', methods=['POST'])
def decline_project_invitation(invitation_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please log in'}), 401
    
    current_user_id = session['user_id']
    invitation = ProjectInvitation.query.get_or_404(invitation_id)
    
    # Check if the invitation is for the current user
    if invitation.recipient_id != current_user_id:
        return jsonify({'success': False, 'message': 'You are not authorized to respond to this invitation'}), 403
    
    # Check if the invitation is pending
    if invitation.status != 'pending':
        return jsonify({'success': False, 'message': 'This invitation has already been processed'}), 400
    
    # Decline the invitation
    invitation.status = 'declined'
    
    # Log the decline
    project = Project.query.get(invitation.project_id)
    new_log = AuditLog(
        user_id=current_user_id,
        action=f'Declined invitation to join project: {project.name if project else "Unknown"}'
    )
    db.session.add(new_log)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'You have declined the invitation'})

@projects_bp.route('/move_task/<int:task_id>', methods=['POST'])
def move_task(task_id):
    """Move a task to a different status column in the Kanban board"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please log in'}), 401
        
    data = request.json
    new_status = data.get('status')
    position = data.get('position', 0)
    
    if not new_status:
        return jsonify({'success': False, 'message': 'Status is required'}), 400
        
    task = Task.query.get_or_404(task_id)
    
    # Check if user has permission (creator or assignee)
    project = Project.query.get(task.project_id)
    user_id = session['user_id']
    
    if user_id != project.created_by and user_id != task.assignee_id and user_id not in [u.user_id for u in project.users]:
        return jsonify({'success': False, 'message': 'Permission denied'}), 403
    
    task.status = new_status
    task.position = position
    task.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    # Log the task movement
    log_entry = AuditLog(
        user_id=user_id,
        action=f"Moved task {task.name} to {new_status} status"
    )
    db.session.add(log_entry)
    db.session.commit()
    
    return jsonify({
        'success': True, 
        'message': 'Task moved successfully',
        'task': {
            'id': task.id,
            'name': task.name,
            'status': task.status,
            'position': task.position
        }
    })

@projects_bp.route('/update_task_priority/<int:task_id>', methods=['POST'])
def update_task_priority(task_id):
    """Update a task's priority"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please log in'}), 401
        
    data = request.json
    new_priority = data.get('priority')
    
    if not new_priority:
        return jsonify({'success': False, 'message': 'Priority is required'}), 400
        
    task = Task.query.get_or_404(task_id)
    
    # Check permissions
    project = Project.query.get(task.project_id)
    user_id = session['user_id']
    
    if user_id != project.created_by and user_id != task.creator_id and user_id != task.assignee_id:
        return jsonify({'success': False, 'message': 'Permission denied'}), 403
    
    task.priority = new_priority
    task.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    # Log the priority change
    log_entry = AuditLog(
        user_id=user_id,
        action=f"Changed priority of task {task.name} to {new_priority}"
    )
    db.session.add(log_entry)
    db.session.commit()
    
    return jsonify({
        'success': True, 
        'message': 'Task priority updated successfully',
        'task': {
            'id': task.id,
            'name': task.name,
            'priority': task.priority
        }
    })

@projects_bp.route('/add_task/<int:project_id>')
def add_task(project_id):
    """Renders the dedicated add task page"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login_user'))
    
    project = Project.query.get_or_404(project_id)
    current_user = User.query.get(session['user_id'])
    
    # Check if user is a member of the project
    is_member = current_user in project.users or project.created_by == current_user.user_id
    if not is_member:
        flash('You do not have access to this project', 'danger')
        return redirect(url_for('projects.manage_projects'))
    
    # Get team members for assignee dropdown
    team_members = list(project.users)
    creator = User.query.get(project.created_by)
    if creator not in team_members:
        team_members.append(creator)
    
    return render_template(
        'add_task.html',
        project=project,
        current_user=current_user,
        team_members=team_members
    )
