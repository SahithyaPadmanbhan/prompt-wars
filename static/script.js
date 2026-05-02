const API_BASE = '/api';

// State
let tasks = [];
let users = [];
let projects = [];
let currentUser = null;
let currentProject = null;

let currentDraggedTask = null;
let statusChartInstance = null;
let priorityChartInstance = null;

// DOM Elements
const userSelector = document.getElementById('user-selector');
const projectSelector = document.getElementById('project-selector');
const projectInfo = document.getElementById('project-info');
const currentUserAvatar = document.getElementById('current-user-avatar');

const modal = document.getElementById('task-modal');
const closeBtn = document.querySelector('.close');
const taskForm = document.getElementById('task-form');
const newTaskBtn = document.getElementById('new-task-btn');
const loadingOverlay = document.getElementById('loading-overlay');
const commentsSection = document.getElementById('task-comments-section');
const commentForm = document.getElementById('comment-form');
const btnSummarize = document.getElementById('btn-summarize');

// Navigation
document.getElementById('nav-board').addEventListener('click', (e) => {
    e.preventDefault();
    switchView('board');
});

document.getElementById('nav-dashboard').addEventListener('click', (e) => {
    e.preventDefault();
    switchView('dashboard');
    renderDashboard();
});

document.getElementById('nav-ai').addEventListener('click', (e) => {
    e.preventDefault();
    switchView('ai');
});

function switchView(view) {
    document.querySelectorAll('.nav-links a').forEach(a => a.classList.remove('active'));
    document.querySelectorAll('.view-container').forEach(v => v.classList.remove('active'));
    
    document.getElementById(`nav-${view}`).classList.add('active');
    document.getElementById(`view-${view}`).classList.add('active');
}

// Fetch and Set Context
async function fetchUsers() {
    try {
        const res = await fetch(`${API_BASE}/users`);
        users = await res.json();
        
        userSelector.innerHTML = '';
        users.forEach(u => {
            const opt = document.createElement('option');
            opt.value = u.id;
            opt.textContent = `${u.name} (${u.role})`;
            userSelector.appendChild(opt);
        });
        
        if (users.length > 0) {
            currentUser = users[0];
            currentUserAvatar.textContent = currentUser.name.charAt(0);
            await fetchProjects();
        }
        
    } catch (err) {
        console.error('Failed to fetch users', err);
    }
}

userSelector.addEventListener('change', async (e) => {
    const id = parseInt(e.target.value);
    currentUser = users.find(u => u.id === id);
    currentUserAvatar.textContent = currentUser.name.charAt(0);
    await fetchProjects();
});

async function fetchProjects() {
    if (!currentUser) return;
    try {
        const res = await fetch(`${API_BASE}/projects?user_id=${currentUser.id}`);
        projects = await res.json();
        
        projectSelector.innerHTML = '<option value="">All Projects</option>';
        projects.forEach(p => {
            const opt = document.createElement('option');
            opt.value = p.id;
            opt.textContent = p.name;
            projectSelector.appendChild(opt);
        });
        
        currentProject = null;
        updateProjectInfo();
        await fetchTasks();
    } catch (err) {
        console.error('Failed to fetch projects', err);
    }
}

projectSelector.addEventListener('change', async (e) => {
    const id = e.target.value;
    currentProject = id ? projects.find(p => p.id == id) : null;
    updateProjectInfo();
    await fetchTasks();
});

function updateProjectInfo() {
    if (currentProject) {
        projectInfo.innerHTML = `<strong>${currentProject.name}</strong> - Scheduled Call: ${currentProject.scheduled_call_time || 'None'}`;
    } else {
        projectInfo.innerHTML = `Showing tasks for ${currentUser.name} (${currentUser.role})`;
    }
}

async function fetchTasks() {
    if (!currentUser) return;
    try {
        let url = `${API_BASE}/tasks?user_id=${currentUser.id}`;
        if (currentProject) {
            url += `&project_id=${currentProject.id}`;
        }
        const res = await fetch(url);
        tasks = await res.json();
        renderBoard();
    } catch (err) {
        console.error('Failed to fetch tasks', err);
    }
}

// Render Board
function renderBoard() {
    // Clear columns
    document.querySelectorAll('.task-list').forEach(col => col.innerHTML = '');
    
    const counts = { todo: 0, in_progress: 0, review: 0, done: 0 };

    tasks.forEach(task => {
        const col = document.querySelector(`#col-${task.status} .task-list`);
        if (col) {
            col.appendChild(createTaskCard(task));
            counts[task.status]++;
        }
    });

    // Update counts
    Object.keys(counts).forEach(status => {
        document.getElementById(`count-${status}`).textContent = counts[status];
    });
    
    if (document.getElementById('view-dashboard').classList.contains('active')) {
        renderDashboard();
    }
}

function renderDashboard() {
    const statusCounts = { todo: 0, in_progress: 0, review: 0, done: 0 };
    const priorityCounts = { low: 0, medium: 0, high: 0 };

    tasks.forEach(task => {
        if (statusCounts[task.status] !== undefined) statusCounts[task.status]++;
        if (priorityCounts[task.priority] !== undefined) priorityCounts[task.priority]++;
    });

    const statusCtx = document.getElementById('statusChart').getContext('2d');
    if (statusChartInstance) statusChartInstance.destroy();
    statusChartInstance = new Chart(statusCtx, {
        type: 'doughnut',
        data: {
            labels: ['To Do', 'In Progress', 'Review', 'Done'],
            datasets: [{
                data: [statusCounts.todo, statusCounts.in_progress, statusCounts.review, statusCounts.done],
                backgroundColor: ['#64748b', '#3b82f6', '#eab308', '#22c55e'],
                borderWidth: 0
            }]
        },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { labels: { color: '#f8fafc' } } } }
    });

    const priorityCtx = document.getElementById('priorityChart').getContext('2d');
    if (priorityChartInstance) priorityChartInstance.destroy();
    priorityChartInstance = new Chart(priorityCtx, {
        type: 'bar',
        data: {
            labels: ['Low', 'Medium', 'High'],
            datasets: [{
                label: 'Tasks',
                data: [priorityCounts.low, priorityCounts.medium, priorityCounts.high],
                backgroundColor: ['#3b82f6', '#eab308', '#ef4444'],
                borderWidth: 0
            }]
        },
        options: { 
            responsive: true, 
            maintainAspectRatio: false, 
            plugins: { legend: { display: false } },
            scales: {
                y: { ticks: { color: '#94a3b8', stepSize: 1 }, grid: { color: 'rgba(255,255,255,0.1)' } },
                x: { ticks: { color: '#94a3b8' }, grid: { display: false } }
            }
        }
    });
}

function createTaskCard(task) {
    const div = document.createElement('div');
    div.className = 'task-card';
    div.draggable = true;
    div.dataset.id = task.id;
    div.dataset.priority = task.priority;
    
    let blockedBadge = task.is_blocked ? '<span class="badge blocked">Blocked</span>' : '';
    
    div.innerHTML = `
        <div class="task-title">${task.title}</div>
        <div class="task-meta">
            <div class="task-assignee">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
                ${task.assignee || 'Unassigned'}
            </div>
            ${blockedBadge}
        </div>
    `;

    div.addEventListener('dragstart', handleDragStart);
    div.addEventListener('dragend', handleDragEnd);
    div.addEventListener('click', () => openTaskModal(task));

    return div;
}

// Drag and Drop
function handleDragStart(e) {
    currentDraggedTask = e.target;
    e.target.style.opacity = '0.5';
}

function handleDragEnd(e) {
    e.target.style.opacity = '1';
    currentDraggedTask = null;
}

function allowDrop(e) {
    e.preventDefault();
}

async function drop(e, status) {
    e.preventDefault();
    if (!currentDraggedTask) return;
    
    const taskId = currentDraggedTask.dataset.id;
    const task = tasks.find(t => t.id == taskId);
    
    if (task.status !== status) {
        task.status = status;
        renderBoard(); // optimistic update
        
        try {
            await fetch(`${API_BASE}/tasks/${taskId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ status: status })
            });
        } catch (err) {
            console.error('Failed to update task status', err);
            fetchTasks(); // revert on failure
        }
    }
}

// Modal Logic
newTaskBtn.addEventListener('click', () => {
    document.getElementById('task-id').value = '';
    document.getElementById('modal-title').textContent = 'Create Task';
    taskForm.reset();
    commentsSection.style.display = 'none';
    modal.classList.add('show');
});

closeBtn.addEventListener('click', () => {
    modal.classList.remove('show');
});

window.addEventListener('click', (e) => {
    if (e.target == modal) {
        modal.classList.remove('show');
    }
});

function openTaskModal(task) {
    document.getElementById('task-id').value = task.id;
    document.getElementById('modal-title').textContent = 'Edit Task';
    document.getElementById('task-title').value = task.title;
    document.getElementById('task-desc').value = task.description || '';
    document.getElementById('task-status').value = task.status;
    document.getElementById('task-priority').value = task.priority;
    document.getElementById('task-assignee').value = task.assignee || '';
    document.getElementById('task-blocked').checked = task.is_blocked;
    
    renderComments(task.comments || []);
    commentsSection.style.display = 'block';
    document.getElementById('ai-summary-box').style.display = 'none';
    
    modal.classList.add('show');
}

taskForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const id = document.getElementById('task-id').value;
    const taskData = {
        title: document.getElementById('task-title').value,
        description: document.getElementById('task-desc').value,
        status: document.getElementById('task-status').value,
        priority: document.getElementById('task-priority').value,
        assignee: document.getElementById('task-assignee').value,
        is_blocked: document.getElementById('task-blocked').checked,
    };
    
    const method = id ? 'PUT' : 'POST';
    const url = id ? `${API_BASE}/tasks/${id}` : `${API_BASE}/tasks`;
    
    try {
        await fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(taskData)
        });
        modal.classList.remove('show');
        fetchTasks();
    } catch (err) {
        console.error('Save failed', err);
    }
});

// Comments
function renderComments(comments) {
    const list = document.getElementById('comments-list');
    list.innerHTML = '';
    comments.forEach(c => {
        const div = document.createElement('div');
        div.className = 'comment';
        div.innerHTML = `
            <div class="comment-author">${c.author}</div>
            <div class="comment-content">${c.content}</div>
        `;
        list.appendChild(div);
    });
}

commentForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const id = document.getElementById('task-id').value;
    if (!id) return;
    
    const input = document.getElementById('comment-input');
    const content = input.value.trim();
    if (!content) return;
    
    try {
        const res = await fetch(`${API_BASE}/tasks/${id}/comments`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ author: currentUser ? currentUser.name : 'Unknown User', content })
        });
        const newComment = await res.json();
        
        const task = tasks.find(t => t.id == id);
        if (task) {
            task.comments.push(newComment);
            renderComments(task.comments);
        }
        input.value = '';
    } catch (err) {
        console.error('Failed to post comment', err);
    }
});

// AI Features
btnSummarize.addEventListener('click', async (e) => {
    e.preventDefault();
    const id = document.getElementById('task-id').value;
    if (!id) return;
    
    loadingOverlay.style.display = 'flex';
    try {
        const res = await fetch(`${API_BASE}/ai/summarize/${id}`);
        const data = await res.json();
        
        const box = document.getElementById('ai-summary-box');
        box.textContent = data.summary;
        box.style.display = 'block';
    } catch (err) {
        console.error('AI Error', err);
    } finally {
        loadingOverlay.style.display = 'none';
    }
});

document.getElementById('ai-standup-btn').addEventListener('click', async () => {
    switchView('ai');
    loadingOverlay.style.display = 'flex';
    
    try {
        let url = `${API_BASE}/ai/standup`;
        if (currentProject) {
            url += `?project_id=${currentProject.id}`;
        }
        const res = await fetch(url);
        const data = await res.json();
        
        const content = document.getElementById('ai-content');
        // Simple markdown parsing for the AI standup (bolding and lists)
        let html = data.standup
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/\n\*/g, '<br>•')
            .replace(/\n/g, '<br>');
            
        content.innerHTML = html;
    } catch (err) {
        console.error('AI Standup Error', err);
    } finally {
        loadingOverlay.style.display = 'none';
    }
});

// Initial load
fetchUsers();
