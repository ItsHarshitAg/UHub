// Global variables
let projectId = document.querySelector('meta[name="project-id"]').getAttribute('content');
let userId = document.querySelector('meta[name="user-id"]').getAttribute('content');

// Initialize the dashboard when the page loads
document.addEventListener('DOMContentLoaded', function() {
    console.log("Dashboard initialized for project:", projectId);
    
    // Check if we're coming back from adding a task
    const urlParams = new URLSearchParams(window.location.search);
    const taskAdded = urlParams.get('task_added');
    const taskId = urlParams.get('task_id');
    
    // Check for success flash message
    const flashMessages = document.querySelectorAll('.alert');
    let hasSuccessFlash = false;
    flashMessages.forEach(msg => {
        if (msg.classList.contains('alert-success') && 
            msg.textContent.includes('Task created successfully')) {
            hasSuccessFlash = true;
        }
    });
    
    // Load initial data
    loadTasks();
    loadChatMessages();
    
    // Set up button handlers
    setupButtonHandlers();
    
    // Show success notification if coming from task creation or if there's a success flash
    if (taskAdded === 'true' || hasSuccessFlash) {
        showNotification('success', 'Task created successfully!');
        // Clean the URL to remove the query parameters
        window.history.replaceState({}, document.title, window.location.pathname);
    }
});

// Show a notification at the top of the page
function showNotification(type, message) {
    const notificationDiv = document.createElement('div');
    notificationDiv.className = `alert alert-${type} alert-dismissible fade show`;
    notificationDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Insert at the top of the container
    const container = document.querySelector('.container-fluid');
    container.insertBefore(notificationDiv, container.firstChild);
    
    // Auto dismiss after 5 seconds
    setTimeout(() => {
        if (notificationDiv.parentElement) {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(notificationDiv);
            bsAlert.close();
        }
    }, 5000);
}

// Load tasks from server with improved error handling and retry mechanism
function loadTasks() {
    console.log("Loading tasks for project:", projectId);
    
    // Show loading state in columns
    document.querySelectorAll('.kanban-body').forEach(column => {
        column.innerHTML = '<div class="text-center p-3"><div class="spinner-border spinner-border-sm text-primary"></div><div class="mt-2 small">Loading tasks...</div></div>';
    });
    
    // Clear any cached data
    const cacheBuster = new Date().getTime();
    
    fetch(`/projects/get_project_tasks/${projectId}?_=${cacheBuster}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                console.log(`Loaded ${data.tasks.length} tasks successfully:`, data.tasks);
                displayTasks(data.tasks);
                
                // Update task counts and progress after loading tasks
                updateTaskStatistics(data.tasks);
            } else {
                console.error("Error loading tasks:", data.message);
                document.querySelectorAll('.kanban-body').forEach(column => {
                    column.innerHTML = `<div class="text-center p-3 text-danger">Error loading tasks: ${data.message}</div>`;
                });
            }
        })
        .catch(error => {
            console.error("Error fetching tasks:", error);
            document.querySelectorAll('.kanban-body').forEach(column => {
                column.innerHTML = `
                    <div class="text-center p-3 text-danger">
                        Failed to load tasks. Please try refreshing the page.
                        <button class="btn btn-sm btn-primary mt-2" onclick="loadTasks()">Retry</button>
                    </div>`;
            });
        });
}

// Add new function to update task statistics
function updateTaskStatistics(tasks) {
    if (!tasks) return;
    
    // Count tasks by status
    const completedTasks = tasks.filter(task => task.status === 'completed').length;
    const totalTasks = tasks.length;
    const pendingTasks = totalTasks - completedTasks;
    
    // Calculate progress percentage
    const progress = totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0;
    
    // Update the UI
    const completedTasksCount = document.getElementById('completedTasksCount');
    const pendingTasksCount = document.getElementById('pendingTasksCount');
    const progressPercentage = document.getElementById('progressPercentage');
    const progressBar = document.getElementById('progressBar');
    
    if (completedTasksCount) completedTasksCount.textContent = completedTasks;
    if (pendingTasksCount) pendingTasksCount.textContent = pendingTasks;
    if (progressPercentage) progressPercentage.textContent = `${progress}%`;
    
    if (progressBar) {
        progressBar.style.width = `${progress}%`;
        progressBar.setAttribute('aria-valuenow', progress);
        progressBar.textContent = `${progress}%`;
    }
}

// Display tasks in their respective columns with better formatting
function displayTasks(tasks) {
    // Clear all columns
    document.querySelectorAll('.kanban-body').forEach(column => {
        if (column) column.innerHTML = '';
    });
    
    // Track if we have any tasks
    let taskCount = 0;
    
    // Add tasks to appropriate columns
    tasks.forEach(task => {
        taskCount++;
        const columnId = `${task.status}Column`;
        const column = document.getElementById(columnId);
        if (!column) {
            console.warn(`Column not found: ${columnId}`);
            return;
        }
        
        const taskCard = document.createElement('div');
        taskCard.className = `task-card priority-${task.priority}`;
        taskCard.id = `task-${task.id}`;
        taskCard.setAttribute('data-task-id', task.id);
        
        // Format due date if exists
        let dueDateDisplay = '';
        if (task.due_date) {
            const dueDate = new Date(task.due_date);
            const today = new Date();
            today.setHours(0, 0, 0, 0);
            
            const dueDateStr = dueDate.toLocaleDateString();
            let dueDateClass = '';
            
            if (dueDate < today) {
                dueDateClass = 'text-danger fw-bold'; // Overdue
            } else if (dueDate.getTime() === today.getTime()) {
                dueDateClass = 'text-warning fw-bold'; // Due today
            }
            
            dueDateDisplay = `<div class="mt-2 small ${dueDateClass}">
                <i class="bi bi-calendar-event me-1"></i> Due: ${dueDateStr}
            </div>`;
        }
        
        // Format assignee if exists
        let assigneeDisplay = '';
        if (task.assignee) {
            assigneeDisplay = `<div class="mt-1 small text-muted">
                <i class="bi bi-person me-1"></i> ${task.assignee}
            </div>`;
        }
        
        // Create task card with formatted content
        taskCard.innerHTML = `
            <div class="d-flex justify-content-between align-items-start mb-2">
                <h5 class="mb-0">${task.name}</h5>
                <span class="badge priority-${task.priority}">${task.priority}</span>
            </div>
            <p class="mb-2 small">${task.description || 'No description'}</p>
            ${assigneeDisplay}
            ${dueDateDisplay}
            <div class="d-flex justify-content-end mt-2">
                <button class="btn btn-sm btn-outline-danger" onclick="deleteTask(${task.id})">
                    <i class="bi bi-trash"></i> Delete
                </button>
            </div>
        `;
        
        column.appendChild(taskCard);
    });
    
    // Display message if no tasks in a column
    document.querySelectorAll('.kanban-body').forEach(column => {
        if (column.children.length === 0) {
            column.innerHTML = '<div class="text-center p-3 text-muted">No tasks yet</div>';
        }
    });
    
    // Display overall message if no tasks at all
    if (taskCount === 0) {
        showNotification('info', 'No tasks yet for this project. Click "Add Task" to create your first task!');
    }
}

// Show the task form
function showTaskForm() {
    document.getElementById('toggleTaskFormBtn').style.display = 'none';
    document.getElementById('inlineTaskForm').style.display = 'block';
    document.getElementById(`newTaskName${projectId}`).focus();
}

// Hide the task form
function hideTaskForm() {
    document.getElementById('inlineTaskForm').style.display = 'none';
    document.getElementById('toggleTaskFormBtn').style.display = 'block';
    document.getElementById(`newTaskForm${projectId}`).reset();
}

// Create a new task
function createNewTask() {
    // Get task data
    const name = document.getElementById(`newTaskName${projectId}`).value.trim();
    const description = document.getElementById(`newTaskDescription${projectId}`).value.trim();
    const priority = document.getElementById(`newTaskPriority${projectId}`).value;
    const dueDate = document.getElementById(`newTaskDueDate${projectId}`).value;
    const assignee = document.getElementById(`newTaskAssignee${projectId}`)?.value;
    
    // Validate
    if (!name) {
        alert('Task name is required');
        return;
    }
    
    // Send to server
    fetch(`/projects/create_task/${projectId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            name,
            description,
            priority,
            due_date: dueDate,
            assignee_id: assignee
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Reload tasks and reset form
            loadTasks();
            hideTaskForm();
        } else {
            alert('Error creating task: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while creating the task');
    });
}

// Delete a task
function deleteTask(taskId) {
    if (!confirm('Are you sure you want to delete this task?')) return;
    
    fetch(`/projects/delete_task/${taskId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            loadTasks();
        } else {
            alert('Error deleting task: ' + data.message);
        }
    })
    .catch(error => console.error('Error:', error));
}

// Load chat messages
function loadChatMessages() {
    fetch(`/projects/get_project_messages/${projectId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const chatContainer = document.getElementById(`chatContainer${projectId}`);
                chatContainer.innerHTML = '';
                
                if (data.messages.length === 0) {
                    chatContainer.innerHTML = '<div class="text-center p-3 text-muted">No messages yet</div>';
                    return;
                }
                
                // Display messages
                data.messages.forEach(msg => {
                    const messageElement = document.createElement('div');
                    messageElement.className = `message-bubble ${msg.sender_id == userId ? 'message-sent' : 'message-received'}`;
                    
                    messageElement.innerHTML = `
                        <strong>${msg.sender_name}</strong>
                        <p>${msg.content}</p>
                        <small class="text-muted">${new Date(msg.timestamp).toLocaleString()}</small>
                    `;
                    
                    chatContainer.appendChild(messageElement);
                });
                
                // Scroll to bottom
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }
        })
        .catch(error => console.error('Error loading chat messages:', error));
}

// Modified chat message sending function with project ID parameter
function sendProjectChatMessage(projectId) {
    const messageInput = document.getElementById(`chatMessageInput${projectId}`);
    const content = messageInput.value.trim();
    
    if (!content) return;
    
    fetch(`/projects/send_project_message/${projectId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            messageInput.value = '';
            loadChatMessages();
        } else {
            alert('Error sending message: ' + data.message);
        }
    })
    .catch(error => console.error('Error:', error));
    
    return false; // Prevent form submission
}

// Set up event handlers for buttons
function setupButtonHandlers() {
    // Task form toggle button
    document.getElementById('toggleTaskFormBtn')?.addEventListener('click', showTaskForm);
    
    // Cancel task button
    document.getElementById('cancelTaskBtn')?.addEventListener('click', hideTaskForm);
    
    // Create task button
    document.getElementById('addTaskButton')?.addEventListener('click', createNewTask);
    
    // Chat form submission - use addEventListener instead of inline onsubmit
    document.getElementById(`chatForm${projectId}`)?.addEventListener('submit', function(e) {
        e.preventDefault();
        sendProjectChatMessage(projectId);
    });
}

// Make functions available globally
window.showTaskForm = showTaskForm;
window.hideTaskForm = hideTaskForm;
window.createNewTask = createNewTask;
window.deleteTask = deleteTask;
window.sendProjectChatMessage = sendProjectChatMessage; // Use the new function name that accepts a parameter