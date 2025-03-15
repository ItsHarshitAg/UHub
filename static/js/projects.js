// Define common skills list
const commonSkills = [
    'Python', 'JavaScript', 'Java', 'C++', 'C#', 'HTML/CSS', 'React', 
    'Angular', 'Vue.js', 'Node.js', 'Express', 'Flask', 'Django', 
    'Spring Boot', 'SQL', 'MongoDB', 'PostgreSQL', 'MySQL', 'Redis',
    'Docker', 'Kubernetes', 'AWS', 'Azure', 'GCP', 'Git', 'CI/CD',
    'Machine Learning', 'Data Science', 'AI', 'Deep Learning', 'NLP',
    'Mobile Development', 'iOS', 'Android', 'Flutter', 'React Native',
    'UI/UX Design', 'Figma', 'Adobe XD', 'Photoshop', 'Illustrator',
    'Project Management', 'Agile', 'Scrum', 'Kanban', 'JIRA',
    'Testing', 'QA', 'Selenium', 'Jest', 'Mocha', 'Cypress',
    'DevOps', 'SRE', 'System Administration', 'Networking', 'Security'
];

/**
 * Initialize Select2 components with default options
 * @param {jQuery} element - The jQuery element to initialize
 */
function initializeSelect2(element) {
    if (!element || element.length === 0) {
        console.error('Invalid element for Select2 initialization');
        return;
    }
    
    // Enhanced Select2 initialization with better defaults and error handling
    try {
        element.select2({
            tags: true,
            tokenSeparators: [',', ' '],
            placeholder: 'Select or type to add skills',
            width: '100%',
            theme: 'bootstrap-5', // Or 'classic' if bootstrap-5 theme is not available
            allowClear: true,
            data: commonSkills.map(skill => ({ id: skill, text: skill })),
            createTag: function(params) {
                const term = $.trim(params.term);
                if (term === '') {
                    return null;
                }
                return {
                    id: term,
                    text: term,
                    newTag: true
                };
            }
        });
        
        // Ensure dropdown opens above if there's not enough space below
        element.on('select2:open', function() {
            const dropdown = $('.select2-dropdown');
            const offset = dropdown.offset();
            const windowHeight = $(window).height();
            
            if (offset && (offset.top + dropdown.outerHeight() > windowHeight)) {
                dropdown.addClass('select2-dropdown--above');
            }
        });
    } catch (e) {
        console.error('Error initializing Select2:', e);
    }
}

/**
 * Fetch project members and display them in a modal
 * @param {number} projectId - The ID of the project
 */
function fetchProjectMembers(projectId) {
    const membersList = document.getElementById("membersList");
    if (!membersList) return;
    
    // Clear existing members
    membersList.innerHTML = "<li class='list-group-item text-center'><div class='spinner-border spinner-border-sm' role='status'></div> Loading members...</li>";
    
    // Fetch project members
    fetch(`/projects/get_project_members/${projectId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`Server responded with status ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            membersList.innerHTML = "";
            if (data.length > 0) {
                data.forEach(member => {
                    const listItem = document.createElement("li");
                    listItem.className = "list-group-item d-flex justify-content-between align-items-center";
                    listItem.textContent = member.name;
                    membersList.appendChild(listItem);
                });
            } else {
                const listItem = document.createElement("li");
                listItem.className = "list-group-item text-center";
                listItem.textContent = "No members found.";
                membersList.appendChild(listItem);
            }
        })
        .catch(error => {
            console.error("Error fetching project members:", error);
            membersList.innerHTML = "<li class='list-group-item text-danger'>Error loading members: " + error.message + "</li>";
        });
}

/**
 * Filter projects based on search term
 * @param {string} searchTerm - The search term to filter by
 */
function filterProjectsBySearch(searchTerm) {
    const projectCards = document.querySelectorAll('.project-card');
    searchTerm = searchTerm.toLowerCase().trim();
    
    projectCards.forEach(card => {
        const projectName = card.dataset.projectName.toLowerCase();
        if (projectName.includes(searchTerm)) {
            card.style.display = '';
        } else {
            card.style.display = 'none';
        }
    });
}

/**
 * Filter projects by type (all, my, joined, available)
 * @param {string} filter - The filter to apply
 */
function filterProjectsByType(filter) {
    const projectCards = document.querySelectorAll('.project-card');
    
    projectCards.forEach(card => {
        if (filter === 'all') {
            card.style.display = '';
        } else {
            const projectType = card.dataset.projectType;
            card.style.display = (projectType === filter) ? '' : 'none';
        }
    });
    
    // Update active button
    const filterButtons = document.querySelectorAll('.project-filter-btn');
    filterButtons.forEach(btn => {
        if (btn.dataset.filter === filter) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
}

/**
 * Submit form with Select2 data appropriately formatted
 * @param {HTMLFormElement} form - The form element to submit
 */
function submitFormWithSelect2Data(form) {
    const select2Element = $(form).find('.select2-enabled');
    if (select2Element.length && select2Element.data('select2')) {
        const skillsArray = select2Element.select2('data').map(item => item.text);
        const skillsString = skillsArray.join(', ');
        
        // Add a hidden field with the skills string
        const hiddenField = document.createElement('input');
        hiddenField.type = 'hidden';
        hiddenField.name = 'required_skills_string';
        hiddenField.value = skillsString;
        form.appendChild(hiddenField);
    }
    return true;
}

/**
 * Initialize all listeners when the document is ready
 */
$(document).ready(function() {
    initializeProjectPage();
    // Initialize the project creation form
    initializeProjectCreationForm();
});

/**
 * Initialize all project page components and event listeners
 */
function initializeProjectPage() {
    // Make sure jQuery and Select2 are available
    if (typeof $ === 'undefined' || typeof $.fn.select2 === 'undefined') {
        console.error('jQuery or Select2 is not loaded properly');
        return;
    }
    
    // Initialize Select2 for main skills selector with a small delay to ensure the DOM is ready
    setTimeout(() => {
        $('.required-skills-select').each(function() {
            // Reset any previous Select2 instances
            if ($(this).data('select2')) {
                $(this).select2('destroy');
            }
            
            initializeSelect2($(this));
            
            // Make sure the select2 container is visible
            const select2Container = $(this).siblings('.select2-container');
            if (select2Container.length) {
                select2Container.css('width', '100%');
                select2Container.show();
            }
        });
        
        // Initialize edit skills selectors
        $('.edit-skills-select').each(function() {
            const $this = $(this);
            initializeSelect2($this);
            
            // Pre-select existing skills for this project
            const projectId = $this.attr('id').replace('edit_required_skills', '');
            const projectSkillsString = $(`#editModal${projectId}`).data('skills') || '';
            if (projectSkillsString) {
                const skillsArray = projectSkillsString.split(',').map(s => s.trim());
                skillsArray.forEach(skill => {
                    if (skill) {
                        const newOption = new Option(skill, skill, true, true);
                        $this.append(newOption);
                    }
                });
                $this.trigger('change');
            }
        });
    }, 100);
    
    // Member list handling
    document.querySelectorAll(".project-name").forEach(projectName => {
        projectName.addEventListener("click", function() {
            const projectId = this.getAttribute("data-project-id");
            fetchProjectMembers(projectId);
        });
    });
    
    // Project search functionality
    const searchInput = document.getElementById('projectSearchInput');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            filterProjectsBySearch(this.value);
        });
    }
    
    // Project type filtering
    const filterButtons = document.querySelectorAll('.project-filter-btn');
    filterButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            filterProjectsByType(this.dataset.filter);
        });
    });
    
    // Form submission handler for creating projects
    const projectForm = document.getElementById('projectForm');
    if (projectForm) {
        projectForm.addEventListener('submit', function(e) {
            return submitFormWithSelect2Data(this);
        });
    }
    
    // Edit form handling
    document.querySelectorAll('.edit-project-form').forEach(form => {
        form.addEventListener('submit', function(e) {
            return submitFormWithSelect2Data(this);
        });
    });
    
    // Initialize Select2 dropdowns when modal is shown
    $('.modal').on('shown.bs.modal', function() {
        $(this).find('select').trigger('change');
    });

    // Initialize skill filters for invitations
    document.querySelectorAll('.skill-filter').forEach(filter => {
        filter.addEventListener('change', function() {
            const projectId = this.dataset.projectId;
            const skill = this.value;
            fetchUsersBySkill(projectId, skill);
        });
    });
    
    // Initialize invitation buttons
    document.querySelectorAll('.invite-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const projectId = this.dataset.projectId;
            sendProjectInvitations(projectId);
        });
    });
    
    // Initialize Kanban board if on project dashboard
    const kanbanBoard = document.querySelector('.kanban-board');
    if (kanbanBoard) {
        const projectId = kanbanBoard.dataset.projectId;
        loadProjectTasks(projectId);
    }
    
    // Initialize project chat if on project dashboard
    const chatContainer = document.querySelector('.chat-container');
    if (chatContainer) {
        const projectId = chatContainer.dataset.projectId;
        loadProjectChat(projectId);
        
        // Set up auto-refresh for chat
        setInterval(() => {
            loadProjectChat(projectId);
        }, 5000);
    }
}

/**
 * Initialize the project creation form with proper setup and form submission
 */
function initializeProjectCreationForm() {
    // Handle form submission
    $('#newProjectForm').on('submit', function(e) {
        e.preventDefault();
        
        // Show loading state
        const submitBtn = $('#submit-project-btn');
        const spinner = $('#submit-spinner');
        const feedback = $('#form-feedback');
        
        submitBtn.prop('disabled', true);
        spinner.removeClass('d-none');
        feedback.addClass('d-none');
        
        // Get form values
        const projectName = $('#project_name').val().trim();
        const projectDescription = $('#project_description').val().trim();
        const requiredSkills = $('#required_skills_input').val().trim();
        
        // Validate form values
        if (!projectName) {
            showFormFeedback('error', 'Project name is required');
            return;
        }
        
        if (!projectDescription) {
            showFormFeedback('error', 'Project description is required');
            return;
        }
        
        if (!requiredSkills) {
            showFormFeedback('error', 'At least one skill is required');
            return;
        }
        
        // Create project data
        const projectData = {
            project_name: projectName,
            project_description: projectDescription,
            required_skills_string: requiredSkills
        };
        
        // Send AJAX request to create project
        $.ajax({
            url: '/projects/manage_projects',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(projectData),
            success: function(response) {
                showFormFeedback('success', 'Project created successfully! Refreshing page...');
                
                // Refresh page after a brief delay
                setTimeout(() => {
                    window.location.reload();
                }, 1500);
            },
            error: function(xhr) {
                let errorMessage = 'Failed to create project. Please try again.';
                if (xhr.responseJSON && xhr.responseJSON.message) {
                    errorMessage = xhr.responseJSON.message;
                }
                showFormFeedback('error', errorMessage);
                
                // Reset button state
                submitBtn.prop('disabled', false);
                spinner.addClass('d-none');
            }
        });
    });
    
    /**
     * Show form feedback message
     * @param {string} type - success or error
     * @param {string} message - feedback message
     */
    function showFormFeedback(type, message) {
        const feedback = $('#form-feedback');
        feedback.removeClass('d-none alert-success alert-danger')
            .addClass(type === 'success' ? 'alert-success' : 'alert-danger')
            .text(message)
            .show();
        
        // Reset button state if error
        if (type === 'error') {
            $('#submit-project-btn').prop('disabled', false);
            $('#submit-spinner').addClass('d-none');
        }
        
        // Scroll to feedback
        feedback[0].scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
}

/**
 * Fetch users by skill for project invitations
 * @param {number} projectId - The project ID
 * @param {string} skill - The skill to filter by (optional)
 */
function fetchUsersBySkill(projectId, skill = '') {
    const userList = document.getElementById(`userList${projectId}`);
    if (!userList) return;
    
    // Show loading state
    userList.innerHTML = '<div class="text-center py-3"><div class="spinner-border text-primary" role="status"></div><p class="mt-2">Loading users...</p></div>';
    
    fetch(`/projects/get_users_by_skill?project_id=${projectId}&skill=${encodeURIComponent(skill)}`)
        .then(response => {
            if (!response.ok) throw new Error('Network response was not ok');
            return response.json();
        })
        .then(data => {
            if (!data.success || !data.users || data.users.length === 0) {
                userList.innerHTML = '<p class="text-center py-3">No matching users found.</p>';
                return;
            }
            
            // Create user cards
            userList.innerHTML = '';
            data.users.forEach(user => {
                const userCard = document.createElement('div');
                userCard.className = 'card mb-2 user-item';
                userCard.innerHTML = `
                    <div class="card-body py-2 px-3">
                        <div class="d-flex justify-content-between align-items-center">
                            <div>
                                <h6 class="mb-0">${user.name}</h6>
                                <p class="text-muted small mb-0">${user.email}</p>
                                <div class="skill-badges mt-1">
                                    ${user.skills.slice(0, 3).map(skill => 
                                        `<span class="badge bg-light text-dark border me-1">${skill}</span>`
                                    ).join('')}
                                    ${user.skills.length > 3 ? 
                                        `<span class="badge bg-light text-dark border">+${user.skills.length - 3} more</span>` : ''}
                                </div>
                            </div>
                            <div>
                                <button class="btn btn-sm btn-outline-primary select-user-btn" 
                                        data-user-id="${user.id}" 
                                        data-user-name="${user.name}">
                                    <i class="bi bi-plus-circle"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                `;
                
                userList.appendChild(userCard);
                
                // Add event listener to select user button
                const selectBtn = userCard.querySelector('.select-user-btn');
                selectBtn.addEventListener('click', function() {
                    const userId = this.dataset.userId;
                    const userName = this.dataset.userName;
                    addSelectedUser(projectId, userId, userName);
                    
                    // Toggle button state
                    if (this.classList.contains('btn-outline-primary')) {
                        this.classList.remove('btn-outline-primary');
                        this.classList.add('btn-outline-danger');
                        this.innerHTML = '<i class="bi bi-dash-circle"></i>';
                    } else {
                        removeSelectedUser(projectId, userId);
                        this.classList.remove('btn-outline-danger');
                        this.classList.add('btn-outline-primary');
                        this.innerHTML = '<i class="bi bi-plus-circle"></i>';
                    }
                });
            });
        })
        .catch(error => {
            console.error('Error fetching users:', error);
            userList.innerHTML = `<p class="text-center text-danger py-3">Error loading users: ${error.message}</p>`;
        });
}

/**
 * Add a user to the selected users list
 * @param {number} projectId - The project ID
 * @param {number} userId - The user ID to add
 * @param {string} userName - The user's name
 */
function addSelectedUser(projectId, userId, userName) {
    const selectedUsers = document.getElementById(`selectedUsers${projectId}`);
    
    // Check if user is already selected
    if (document.querySelector(`.selected-user-badge[data-user-id="${userId}"]`)) {
        return;
    }
    
    const userBadge = document.createElement('div');
    userBadge.className = 'selected-user-badge badge bg-primary m-1';
    userBadge.dataset.userId = userId;
    userBadge.innerHTML = `
        ${userName} 
        <button type="button" class="btn-close btn-close-white ms-1" 
                aria-label="Remove" style="font-size: 0.5rem;"
                onclick="removeSelectedUser('${projectId}', '${userId}')"></button>
    `;
    
    selectedUsers.appendChild(userBadge);
}

/**
 * Remove a user from the selected users list
 * @param {number} projectId - The project ID
 * @param {number} userId - The user ID to remove
 */
function removeSelectedUser(projectId, userId) {
    const badge = document.querySelector(`.selected-user-badge[data-user-id="${userId}"]`);
    if (badge) {
        badge.remove();
    }
    
    // Reset the add button if it exists
    const addBtn = document.querySelector(`.select-user-btn[data-user-id="${userId}"]`);
    if (addBtn) {
        addBtn.classList.remove('btn-outline-danger');
        addBtn.classList.add('btn-outline-primary');
        addBtn.innerHTML = '<i class="bi bi-plus-circle"></i>';
    }
}

/**
 * Send project invitations to selected users
 * @param {number} projectId - The project ID
 */
function sendProjectInvitations(projectId) {
    const selectedUserElements = document.querySelectorAll(`#selectedUsers${projectId} .selected-user-badge`);
    const recipientIds = Array.from(selectedUserElements).map(el => el.dataset.userId);
    
    if (recipientIds.length === 0) {
        alert('Please select at least one user to invite.');
        return;
    }
    
    const message = document.getElementById(`inviteMessage${projectId}`).value;
    
    fetch(`/projects/invite_to_project/${projectId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 
            recipient_ids: recipientIds,
            message: message
        })
    })
    .then(response => {
        if (!response.ok) throw new Error('Network response was not ok');
        return response.json();
    })
    .then(data => {
        if (data.success) {
            alert(data.message);
            // Close the modal
            $(`#inviteModal${projectId}`).modal('hide');
        } else {
            alert('Error: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error sending invitations:', error);
        alert('Failed to send invitations: ' + error.message);
    });
}

// Task management functions
/**
 * Create a new task for a project
 * @param {number} projectId - The project ID
 */
function createTask(projectId) {
    const name = document.getElementById(`newTaskName${projectId}`).value;
    const description = document.getElementById(`newTaskDescription${projectId}`).value;
    const assigneeId = document.getElementById(`newTaskAssignee${projectId}`).value;
    const priority = document.getElementById(`newTaskPriority${projectId}`).value;
    const dueDate = document.getElementById(`newTaskDueDate${projectId}`).value;
    
    if (!name) {
        alert('Task name is required');
        return;
    }
    
    const taskData = {
        name: name,
        description: description,
        assignee_id: assigneeId || null,
        priority: priority || 'medium',
        due_date: dueDate || null
    };
    
    fetch(`/projects/create_task/${projectId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(taskData)
    })
    .then(response => {
        if (!response.ok) throw new Error('Network response was not ok');
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // Refresh tasks
            loadProjectTasks(projectId);
            
            // Clear form
            document.getElementById(`newTaskForm${projectId}`).reset();
            
            // Close modal if it exists
            const modal = document.getElementById('createTaskModal');
            if (modal) {
                const bsModal = bootstrap.Modal.getInstance(modal);
                if (bsModal) bsModal.hide();
            }
        } else {
            alert('Error: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error creating task:', error);
        alert('Failed to create task: ' + error.message);
    });
}

/**
 * Load tasks for a project
 * @param {number} projectId - The project ID
 */
function loadProjectTasks(projectId) {
    fetch(`/projects/get_project_tasks/${projectId}`)
        .then(response => {
            if (!response.ok) throw new Error('Network response was not ok');
            return response.json();
        })
        .then(data => {
            if (!data.success) {
                console.error('Error loading tasks:', data.message);
                return;
            }
            
            // Clear task boards
            const columns = ['todo', 'in_progress', 'review', 'completed'];
            columns.forEach(column => {
                const columnEl = document.getElementById(`${column}Column`);
                if (columnEl) columnEl.innerHTML = '';
            });
            
            // Add tasks to columns
            data.tasks.forEach(task => {
                addTaskToBoard(task);
            });
            
            // Initialize drag and drop for tasks
            initializeDragAndDrop();
        })
        .catch(error => {
            console.error('Error loading tasks:', error);
        });
}

/**
 * Add a task to the Kanban board
 * @param {Object} task - The task object
 */
function addTaskToBoard(task) {
    const columnId = `${task.status}Column`;
    const column = document.getElementById(columnId);
    if (!column) return;
    
    const taskCard = document.createElement('div');
    taskCard.className = `task-card priority-${task.priority}`;
    taskCard.id = `task-${task.id}`;
    taskCard.draggable = true;
    
    let assigneeText = task.assignee ? `<small class="text-muted">Assigned to: ${task.assignee}</small>` : 
                                      '<small class="text-muted">Unassigned</small>';
    
    let dueDate = task.due_date ? 
                  `<small class="text-muted d-block mt-1">Due: ${new Date(task.due_date).toLocaleDateString()}</small>` : '';
    
    taskCard.innerHTML = `
        <div class="d-flex justify-content-between align-items-start">
            <h6 class="mb-1 task-name">${task.name}</h6>
            <span class="badge priority-${task.priority}">${task.priority}</span>
        </div>
        <p class="mb-1 small task-description">${task.description || ''}</p>
        ${assigneeText}
        ${dueDate}
        <div class="task-actions mt-2">
            <button class="btn btn-sm btn-outline-primary edit-task-btn" 
                    onclick="editTask(${task.id})">
                <i class="bi bi-pencil"></i>
            </button>
            <button class="btn btn-sm btn-outline-danger delete-task-btn" 
                    onclick="deleteTask(${task.id})">
                <i class="bi bi-trash"></i>
            </button>
        </div>
    `;
    
    // Add drag events
    taskCard.addEventListener('dragstart', e => {
        e.dataTransfer.setData('text/plain', task.id);
        setTimeout(() => {
            taskCard.classList.add('dragging');
        }, 0);
    });
    
    taskCard.addEventListener('dragend', () => {
        taskCard.classList.remove('dragging');
    });
    
    column.appendChild(taskCard);
}

/**
 * Initialize drag and drop functionality for the Kanban board
 */
function initializeDragAndDrop() {
    const columns = document.querySelectorAll('.kanban-body');
    
    columns.forEach(column => {
        column.addEventListener('dragover', e => {
            e.preventDefault();
            column.classList.add('dragover');
        });
        
        column.addEventListener('dragleave', () => {
            column.classList.remove('dragover');
        });
        
        column.addEventListener('drop', e => {
            e.preventDefault();
            column.classList.remove('dragover');
            
            const taskId = e.dataTransfer.getData('text/plain');
            const status = column.id.replace('Column', '');
            
            // Move task in the UI
            const taskElement = document.getElementById(`task-${taskId}`);
            if (taskElement) {
                column.appendChild(taskElement);
            }
            
            // Update the task status on the server
            moveTask(taskId, status);
        });
    });
}

/**
 * Move a task to a different column/status
 * @param {number} taskId - The task ID
 * @param {string} newStatus - The new status
 */
function moveTask(taskId, newStatus) {
    fetch(`/projects/move_task/${taskId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ status: newStatus })
    })
    .then(response => {
        if (!response.ok) throw new Error('Network response was not ok');
        return response.json();
    })
    .then(data => {
        if (!data.success) {
            alert('Error: ' + data.message);
            // Reload tasks to revert UI
            loadProjectTasks(data.task.project_id);
        }
    })
    .catch(error => {
        console.error('Error moving task:', error);
        alert('Failed to update task status. Please try again.');
    });
}

/**
 * Delete a task
 * @param {number} taskId - The task ID to delete
 */
function deleteTask(taskId) {
    if (!confirm('Are you sure you want to delete this task?')) {
        return;
    }
    
    fetch(`/projects/delete_task/${taskId}`, {
        method: 'DELETE'
    })
    .then(response => {
        if (!response.ok) throw new Error('Network response was not ok');
        return response.json();
    })
    .then(data => {
        if (data.success) {
            const taskElement = document.getElementById(`task-${taskId}`);
            if (taskElement) {
                taskElement.remove();
            }
        } else {
            alert('Error: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error deleting task:', error);
        alert('Failed to delete task: ' + error.message);
    });
}

/**
 * Load and display project chat messages
 * @param {number} projectId - The project ID
 */
function loadProjectChat(projectId) {
    const chatContainer = document.getElementById(`chatContainer${projectId}`);
    if (!chatContainer) return;
    
    fetch(`/projects/get_project_messages/${projectId}`)
        .then(response => {
            if (!response.ok) throw new Error('Network response was not ok');
            return response.json();
        })
        .then(data => {
            if (!data.success) {
                console.error('Error loading chat messages:', data.message);
                return;
            }
            
            chatContainer.innerHTML = '';
            
            if (data.messages.length === 0) {
                chatContainer.innerHTML = '<div class="text-center text-muted p-3">No messages yet. Start the conversation!</div>';
                return;
            }
            
            // Current user ID to distinguish sent vs received messages
            const currentUserId = document.querySelector('meta[name="user-id"]')?.content;
            
            data.messages.forEach(msg => {
                const messageClass = msg.sender_id.toString() === currentUserId ? 'message-sent' : 'message-received';
                
                const messageEl = document.createElement('div');
                messageEl.className = `message-bubble ${messageClass}`;
                
                // Format timestamp
                const timestamp = new Date(msg.timestamp);
                const formattedTime = timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                const formattedDate = timestamp.toLocaleDateString();
                
                messageEl.innerHTML = `
                    <div>
                        <small class="message-sender">${msg.sender_name}</small>
                        <p class="mb-0">${msg.content}</p>
                        <small class="message-time text-muted">${formattedTime} | ${formattedDate}</small>
                    </div>
                `;
                
                chatContainer.appendChild(messageEl);
            });
            
            // Scroll to bottom
            chatContainer.scrollTop = chatContainer.scrollHeight;
        })
        .catch(error => {
            console.error('Error loading chat:', error);
            chatContainer.innerHTML = `<div class="text-center text-danger p-3">Error loading chat: ${error.message}</div>`;
        });
}

/**
 * Send a message in the project chat
 * @param {number} projectId - The project ID
 */
function sendProjectMessage(projectId) {
    const messageInput = document.getElementById(`chatMessageInput${projectId}`);
    const content = messageInput.value.trim();
    
    if (!content) return;
    
    fetch(`/projects/send_project_message/${projectId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ content })
    })
    .then(response => {
        if (!response.ok) throw new Error('Network response was not ok');
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // Clear input
            messageInput.value = '';
            
            // Refresh chat
            loadProjectChat(projectId);
        } else {
            console.error('Error sending message:', data.message);
        }
    })
    .catch(error => {
        console.error('Error sending message:', error);
        alert('Failed to send message: ' + error.message);
    });
}

// Enhanced initialization function
function initializeProjectPage() {
    // Initialize Select2 for main skills selector
    if (typeof $.fn.select2 !== 'undefined') {
        // Initialize main skills selector
        initializeSelect2($('.required-skills-select'));
        
        // Initialize edit skills selectors
        $('.edit-skills-select').each(function() {
            const $this = $(this);
            initializeSelect2($this);
            
            // Pre-select existing skills for this project
            const projectId = $this.attr('id').replace('edit_required_skills', '');
            const projectSkillsString = $(`#editModal${projectId}`).data('skills') || '';
            if (projectSkillsString) {
                const skillsArray = projectSkillsString.split(',').map(s => s.trim());
                skillsArray.forEach(skill => {
                    if (skill) {
                        const newOption = new Option(skill, skill, true, true);
                        $this.append(newOption);
                    }
                });
                $this.trigger('change');
            }
        });
    } else {
        console.error('jQuery or Select2 not loaded properly');
    }
    
    // Member list handling
    document.querySelectorAll(".project-name").forEach(projectName => {
        projectName.addEventListener("click", function() {
            const projectId = this.getAttribute("data-project-id");
            fetchProjectMembers(projectId);
        });
    });
    
    // Project search functionality
    const searchInput = document.getElementById('projectSearchInput');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            filterProjectsBySearch(this.value);
        });
    }
    
    // Project type filtering
    const filterButtons = document.querySelectorAll('.project-filter-btn');
    filterButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            filterProjectsByType(this.dataset.filter);
        });
    });
    
    // Form submission handler for creating projects
    const projectForm = document.getElementById('projectForm');
    if (projectForm) {
        projectForm.addEventListener('submit', function(e) {
            return submitFormWithSelect2Data(this);
        });
    }
    
    // Edit form handling
    document.querySelectorAll('.edit-project-form').forEach(form => {
        form.addEventListener('submit', function(e) {
            return submitFormWithSelect2Data(this);
        });
    });
    
    // Initialize Select2 dropdowns when modal is shown
    $('.modal').on('shown.bs.modal', function() {
        $(this).find('select').trigger('change');
    });

    // Initialize skill filters for invitations
    document.querySelectorAll('.skill-filter').forEach(filter => {
        filter.addEventListener('change', function() {
            const projectId = this.dataset.projectId;
            const skill = this.value;
            fetchUsersBySkill(projectId, skill);
        });
    });
    
    // Initialize invitation buttons
    document.querySelectorAll('.invite-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const projectId = this.dataset.projectId;
            sendProjectInvitations(projectId);
        });
    });
    
    // Initialize Kanban board if on project dashboard
    const kanbanBoard = document.querySelector('.kanban-board');
    if (kanbanBoard) {
        const projectId = kanbanBoard.dataset.projectId;
        loadProjectTasks(projectId);
    }
    
    // Initialize project chat if on project dashboard
    const chatContainer = document.querySelector('.chat-container');
    if (chatContainer) {
        const projectId = chatContainer.dataset.projectId;
        loadProjectChat(projectId);
        
        // Set up auto-refresh for chat
        setInterval(() => {
            loadProjectChat(projectId);
        }, 5000);
    }
}

/**
 * Prepare skills data for edit form before submission
 * @param {number} projectId - The ID of the project being edited
 */
function prepareEditSkillsData(projectId) {
    const skillsSelect = document.getElementById(`edit_required_skills${projectId}`);
    const skillsStringField = document.getElementById(`edit_required_skills_string${projectId}`);
    
    if (skillsSelect && skillsStringField) {
        // For Select2 widgets
        if ($(skillsSelect).data('select2')) {
            const select2Data = $(skillsSelect).select2('data');
            const selectedSkills = select2Data.map(item => item.text);
            skillsStringField.value = selectedSkills.join(', ');
        } else {
            // Fallback for regular select
            const selectedSkills = Array.from(skillsSelect.selectedOptions).map(option => option.value);
            skillsStringField.value = selectedSkills.join(', ');
        }
    }
}
/**
 * Prepare skills data before form submission
 * Updates the hidden required_skills_string field with a comma-separated list of skills
 */
function prepareSkillsData() {
    const skillsSelect = document.getElementById('required_skills');
    const skillsStringField = document.getElementById('required_skills_string');
    
    if (skillsSelect && skillsStringField) {
        // Get all selected skills
        const selectedSkills = Array.from(skillsSelect.selectedOptions).map(option => option.value);
        
        // Also get any tags added via Select2 that might not be in the original options
        if ($(skillsSelect).data('select2')) {
            const select2Data = $(skillsSelect).select2('data');
            select2Data.forEach(item => {
                if (!selectedSkills.includes(item.text)) {
                    selectedSkills.push(item.text);
                }
            });
        }
        
        // Update the hidden field with comma-separated list
        skillsStringField.value = selectedSkills.join(', ');
    }
    
    return true;
}

// Add this code to the existing file, replacing any modal-related functions

// Function to show an action section for a project
function showProjectAction(action, projectId) {
    let sectionId;
    
    switch(action) {
        case 'edit':
            sectionId = `editProjectSection${projectId}`;
            break;
        case 'delete':
            sectionId = `deleteProjectSection${projectId}`;
            break;
        case 'join':
            sectionId = `joinProjectSection${projectId}`;
            break;
        case 'leave':
            sectionId = `leaveProjectSection${projectId}`;
            break;
        case 'invite':
            sectionId = `inviteSection${projectId}`;
            break;
        default:
            console.error(`Unknown action: ${action}`);
            return;
    }
    
    showProjectSection(sectionId, projectId);
}

// Update project card actions to use the new inline approach instead of modals
function setupProjectCardActions() {
    // Find all action buttons in project cards
    document.querySelectorAll('.project-action-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            
            const action = this.dataset.action;
            const projectId = this.dataset.projectId;
            
            // Show appropriate section
            showProjectAction(action, projectId);
        });
    });
}

// Call this on page load
document.addEventListener('DOMContentLoaded', function() {
    // ...existing code...
    
    setupProjectCardActions();
    
    // ...existing code...
});
