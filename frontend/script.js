document.addEventListener('DOMContentLoaded', () => {
    // API Endpoint (proxied via Nginx /api/ or direct)
    const API_URL = '/api/tasks';

    // State management
    let tasksState = [];
    let currentFilter = 'all';

    // DOM Elements
    const taskForm = document.getElementById('task-form');
    const taskTitleInput = document.getElementById('task-title');
    const taskDescInput = document.getElementById('task-desc');
    const btnSubmit = document.getElementById('btn-submit');
    const taskListContainer = document.getElementById('task-list');
    const loadingSpinner = document.getElementById('loading-spinner');
    const emptyState = document.getElementById('empty-state');
    const toastContainer = document.getElementById('toast-container');
    const filterTabs = document.querySelectorAll('.tab-btn');

    // Stats Elements
    const statTotal = document.getElementById('stat-total');
    const statPending = document.getElementById('stat-pending');
    const statCompleted = document.getElementById('stat-completed');

    // Initialize application
    fetchTasks();
    setupEventListeners();

    function setupEventListeners() {
        // Form submission
        taskForm.addEventListener('submit', handleTaskSubmit);

        // Filter tab switching
        filterTabs.forEach(tab => {
            tab.addEventListener('click', (e) => {
                filterTabs.forEach(t => t.classList.remove('active'));
                e.target.classList.add('active');
                currentFilter = e.target.getAttribute('data-filter');
                renderTasks();
            });
        });
    }

    /**
     * Fetch all tasks from Flask backend API
     */
    async function fetchTasks() {
        showLoading(true);
        try {
            const response = await fetch(API_URL);
            const result = await response.json();

            if (response.ok && result.success) {
                tasksState = result.data || [];
                updateStats();
                renderTasks();
            } else {
                showToast(result.error || 'Failed to load tasks', 'error');
            }
        } catch (error) {
            console.error('Error fetching tasks:', error);
            showToast('Unable to connect to backend server', 'error');
        } finally {
            showLoading(false);
        }
    }

    /**
     * Handle new task creation
     */
    async function handleTaskSubmit(e) {
        e.preventDefault();

        const title = taskTitleInput.value.trim();
        const description = taskDescInput.value.trim();

        if (!title) {
            showToast('Please enter a task title', 'error');
            return;
        }

        btnSubmit.disabled = true;
        btnSubmit.innerHTML = '<span>Saving...</span>';

        try {
            const response = await fetch(API_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title, description })
            });

            const result = await response.json();

            if (response.ok && result.success) {
                showToast('Task created successfully!', 'success');
                taskTitleInput.value = '';
                taskDescInput.value = '';
                await fetchTasks();
            } else {
                showToast(result.error || 'Failed to create task', 'error');
            }
        } catch (error) {
            console.error('Error creating task:', error);
            showToast('Failed to reach server. Please try again.', 'error');
        } finally {
            btnSubmit.disabled = false;
            btnSubmit.innerHTML = '<span class="btn-icon">+</span> Add Task';
        }
    }

    /**
     * Toggle task completion status
     */
    async function toggleTaskStatus(taskId, currentStatus) {
        const newStatus = currentStatus === 'completed' ? 'pending' : 'completed';

        try {
            const response = await fetch(`${API_URL}/${taskId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ status: newStatus })
            });

            const result = await response.json();

            if (response.ok && result.success) {
                showToast(`Task marked as ${newStatus}!`, 'success');
                await fetchTasks();
            } else {
                showToast(result.error || 'Failed to update task status', 'error');
            }
        } catch (error) {
            console.error('Error updating task:', error);
            showToast('Server connection error', 'error');
        }
    }

    /**
     * Delete a task by ID
     */
    async function deleteTask(taskId) {
        if (!confirm('Are you sure you want to delete this task?')) return;

        try {
            const response = await fetch(`${API_URL}/${taskId}`, {
                method: 'DELETE'
            });

            const result = await response.json();

            if (response.ok && result.success) {
                showToast('Task deleted successfully!', 'success');
                await fetchTasks();
            } else {
                showToast(result.error || 'Failed to delete task', 'error');
            }
        } catch (error) {
            console.error('Error deleting task:', error);
            showToast('Server connection error', 'error');
        }
    }

    /**
     * Render task list based on selected filter
     */
    function renderTasks() {
        taskListContainer.innerHTML = '';

        const filteredTasks = tasksState.filter(task => {
            if (currentFilter === 'pending') return task.status === 'pending';
            if (currentFilter === 'completed') return task.status === 'completed';
            return true;
        });

        if (filteredTasks.length === 0) {
            emptyState.classList.remove('hidden');
            return;
        } else {
            emptyState.classList.add('hidden');
        }

        filteredTasks.forEach(task => {
            const taskElement = document.createElement('div');
            const isCompleted = task.status === 'completed';
            taskElement.className = `task-item ${isCompleted ? 'completed' : ''}`;

            const formattedDate = formatDate(task.created_at);

            taskElement.innerHTML = `
                <div class="task-content">
                    <div class="task-meta">
                        <span class="badge ${isCompleted ? 'badge-completed' : 'badge-pending'}">
                            ${task.status}
                        </span>
                        <span class="task-time">${formattedDate}</span>
                    </div>
                    <h3 class="task-title-text">${escapeHtml(task.title)}</h3>
                    ${task.description ? `<p class="task-description">${escapeHtml(task.description)}</p>` : ''}
                </div>
                <div class="task-actions">
                    <button class="btn btn-action ${isCompleted ? 'btn-undo' : 'btn-complete'}" data-id="${task.id}" data-status="${task.status}">
                        ${isCompleted ? 'Undo' : 'Complete'}
                    </button>
                    <button class="btn btn-action btn-delete" data-id="${task.id}">
                        Delete
                    </button>
                </div>
            `;

            // Event listeners for task action buttons
            const toggleBtn = taskElement.querySelector('.btn-complete, .btn-undo');
            const deleteBtn = taskElement.querySelector('.btn-delete');

            toggleBtn.addEventListener('click', () => toggleTaskStatus(task.id, task.status));
            deleteBtn.addEventListener('click', () => deleteTask(task.id));

            taskListContainer.appendChild(taskElement);
        });
    }

    /**
     * Update stats counters
     */
    function updateStats() {
        const total = tasksState.length;
        const pending = tasksState.filter(t => t.status === 'pending').length;
        const completed = tasksState.filter(t => t.status === 'completed').length;

        statTotal.textContent = total;
        statPending.textContent = pending;
        statCompleted.textContent = completed;
    }

    /**
     * Helper to show/hide loading spinner
     */
    function showLoading(isLoading) {
        if (isLoading) {
            loadingSpinner.classList.remove('hidden');
            emptyState.classList.add('hidden');
        } else {
            loadingSpinner.classList.add('hidden');
        }
    }

    /**
     * Display toast message
     */
    function showToast(message, type = 'success') {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;

        toastContainer.appendChild(toast);

        setTimeout(() => {
            toast.remove();
        }, 3500);
    }

    /**
     * Utility to format timestamps
     */
    function formatDate(dateString) {
        if (!dateString) return '';
        const date = new Date(dateString);
        if (isNaN(date.getTime())) return dateString;
        return date.toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    /**
     * Escape HTML helper to prevent XSS
     */
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
});
