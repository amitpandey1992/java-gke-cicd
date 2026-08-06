document.addEventListener('DOMContentLoaded', () => {
    // API Endpoints (Nginx proxies these to the respective GKE services)
    const TASKS_API = '/api/tasks';
    const QUOTES_API = '/api/quotes';

    // DOM Elements
    const todoContainer = document.getElementById('cards-todo');
    const progressContainer = document.getElementById('cards-progress');
    const doneContainer = document.getElementById('cards-done');

    const todoCount = document.getElementById('count-todo');
    const progressCount = document.getElementById('count-progress');
    const doneCount = document.getElementById('count-done');

    const taskForm = document.getElementById('task-form');
    const quoteText = document.getElementById('quote-text');
    const btnRefreshQuote = document.getElementById('btn-refresh-quote');

    // Load initial data
    fetchQuote();
    fetchTasks();

    // Event Listeners
    taskForm.addEventListener('submit', handleAddTask);
    btnRefreshQuote.addEventListener('click', fetchQuote);

    // Fetch Quote from quote-service
    async function fetchQuote() {
        quoteText.textContent = "Loading new inspiration...";
        try {
            const response = await fetch(QUOTES_API);
            if (!response.ok) throw new Error('API failed');
            const data = await response.json();
            quoteText.textContent = data.quote;
        } catch (error) {
            console.error('Failed to fetch quote:', error);
            quoteText.textContent = "Work hard, dream big. Success is not final, failure is not fatal.";
        }
    }

    // Fetch Tasks from task-service
    async function fetchTasks() {
        try {
            const response = await fetch(TASKS_API);
            if (!response.ok) throw new Error('Failed to fetch tasks');
            const tasks = await response.json();
            renderTasks(tasks);
        } catch (error) {
            console.error('Error fetching tasks:', error);
        }
    }

    // Render Tasks on Kanban Board
    function renderTasks(tasks) {
        // Clear containers
        todoContainer.innerHTML = '';
        progressContainer.innerHTML = '';
        doneContainer.innerHTML = '';

        let todo = 0, progress = 0, done = 0;

        tasks.forEach(task => {
            const card = createTaskCard(task);
            if (task.status === 'TO_DO') {
                todoContainer.appendChild(card);
                todo++;
            } else if (task.status === 'IN_PROGRESS') {
                progressContainer.appendChild(card);
                progress++;
            } else if (task.status === 'DONE') {
                doneContainer.appendChild(card);
                done++;
            }
        });

        // Update counts
        todoCount.textContent = todo;
        progressCount.textContent = progress;
        doneCount.textContent = done;
    }

    // Create Card DOM element
    function createTaskCard(task) {
        const card = document.createElement('div');
        card.className = 'task-card';
        card.innerHTML = `
            <h3>${escapeHtml(task.title)}</h3>
            <p>${escapeHtml(task.description)}</p>
            <div class="card-actions">
                ${task.status !== 'TO_DO' ? `
                    <button class="btn-icon btn-icon-todo" onclick="updateStatus(${task.id}, 'TO_DO')" title="Move to To Do">
                        <i class="fa-solid fa-arrow-left"></i>
                    </button>
                ` : ''}
                ${task.status !== 'IN_PROGRESS' ? `
                    <button class="btn-icon btn-icon-progress" onclick="updateStatus(${task.id}, 'IN_PROGRESS')" title="Move to In Progress">
                        <i class="fa-solid fa-spinner"></i>
                    </button>
                ` : ''}
                ${task.status !== 'DONE' ? `
                    <button class="btn-icon btn-icon-done" onclick="updateStatus(${task.id}, 'DONE')" title="Mark as Completed">
                        <i class="fa-solid fa-check"></i>
                    </button>
                ` : ''}
                <button class="btn-icon btn-icon-delete" onclick="deleteTask(${task.id})" title="Delete Task">
                    <i class="fa-solid fa-trash-can"></i>
                </button>
            </div>
        `;
        return card;
    }

    // Handle Create Task
    async function handleAddTask(e) {
        e.preventDefault();
        const titleInput = document.getElementById('task-title');
        const descInput = document.getElementById('task-desc');

        const newTask = {
            title: titleInput.value.trim(),
            description: descInput.value.trim(),
            status: 'TO_DO'
        };

        try {
            const response = await fetch(TASKS_API, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(newTask)
            });

            if (!response.ok) throw new Error('Failed to create task');
            titleInput.value = '';
            descInput.value = '';
            fetchTasks(); // Refresh board
        } catch (error) {
            console.error('Error creating task:', error);
        }
    }

    // Update Status (Globally accessible helper)
    window.updateStatus = async (id, status) => {
        try {
            // Fetch the existing task details first
            const res = await fetch(`${TASKS_API}`);
            const tasks = await res.json();
            const task = tasks.find(t => t.id === id);
            
            task.status = status;

            const response = await fetch(`${TASKS_API}/${id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(task)
            });

            if (!response.ok) throw new Error('Failed to update status');
            fetchTasks();
        } catch (error) {
            console.error('Error updating task:', error);
        }
    };

    // Delete Task (Globally accessible helper)
    window.deleteTask = async (id) => {
        if (!confirm('Are you sure you want to delete this task?')) return;
        try {
            const response = await fetch(`${TASKS_API}/${id}`, {
                method: 'DELETE'
            });

            if (!response.ok) throw new Error('Failed to delete task');
            fetchTasks();
        } catch (error) {
            console.error('Error deleting task:', error);
        }
    };

    // Prevent HTML Injection
    function escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, m => map[m]);
    }
});
