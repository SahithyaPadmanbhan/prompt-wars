const API_BASE = '/api';

// State
let tasks = [];
let users = [];
let projects = [];
let currentUser = null;
let currentProject = null;
let filterType = 'team'; // 'me' or 'team'

let currentDraggedTask = null;
let statusChartInstance = null;
let priorityChartInstance = null;
let projectChartInstance = null;

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

// Project Modal Elements
const projectModal = document.getElementById('project-modal');
const newProjectBtn = document.getElementById('new-project-btn');
const closeProjectBtn = document.getElementById('close-project-modal');
const projectForm = document.getElementById('project-form');

// Navigation
document.getElementById('nav-overview').addEventListener('click', (e) => {
    e.preventDefault();
    switchView('overview');
    renderOverview();
});

document.getElementById('nav-dashboard').addEventListener('click', (e) => {
    e.preventDefault();
    switchView('dashboard');
    renderDashboard();
});

document.getElementById('nav-board').addEventListener('click', (e) => {
    e.preventDefault();
    switchView('board');
});

document.getElementById('nav-ai').addEventListener('click', async (e) => {
    e.preventDefault();
    switchView('ai');
    await fetchProjectInsights();
});

function switchView(view) {
    document.querySelectorAll('.nav-links a').forEach(a => a.classList.remove('active'));
    document.querySelectorAll('.view-container').forEach(v => v.classList.remove('active'));
    
    document.getElementById(`nav-${view}`).classList.add('active');
    document.getElementById(`view-${view}`).classList.add('active');
    
    // Update Header Title
    const titleMap = {
        'overview': 'Project Overview',
        'dashboard': 'Dashboard',
        'board': 'Activity Board',
        'ai': 'AI Project Insights'
    };
    const titleEl = document.getElementById('main-view-title');
    if (titleEl) {
        titleEl.textContent = titleMap[view] || 'Activity Board';
    }
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
            opt.textContent = u.name;
            userSelector.appendChild(opt);
        });
        
        // Populate assignee dropdown in the task modal
        const assigneeSelect = document.getElementById('task-assignee');
        assigneeSelect.innerHTML = '<option value="">-- Unassigned --</option>';
        users.forEach(u => {
            const opt = document.createElement('option');
            opt.value = u.id;
            opt.textContent = u.name;
            assigneeSelect.appendChild(opt);
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
        const modalProjectSelector = document.getElementById('task-project-id');
        modalProjectSelector.innerHTML = '<option value="">-- No Project --</option>';
        
        projects.forEach(p => {
            const opt = document.createElement('option');
            opt.value = p.id;
            opt.textContent = p.name;
            projectSelector.appendChild(opt);
            
            const modalOpt = document.createElement('option');
            modalOpt.value = p.id;
            modalOpt.textContent = p.name;
            modalProjectSelector.appendChild(modalOpt);
        });
        
        currentProject = null;
        updateProjectInfo();
        await fetchTasks();
        
        // If we are on the overview page, re-render it
        if (document.getElementById('view-overview').classList.contains('active')) {
            renderOverview();
        }
    } catch (err) {
        console.error('Failed to fetch projects', err);
    }
}

function renderOverview() {
    const list = document.getElementById('project-overview-list');
    list.innerHTML = '';
    
    projects.forEach(p => {
        const div = document.createElement('div');
        div.className = 'dashboard-card glass-panel project-card';
        div.style.borderLeft = '4px solid var(--accent-primary)';
        
        div.innerHTML = `
            <h3>${p.name}</h3>
            <p style="color: var(--text-secondary); margin: 10px 0;">Scheduled Call: ${p.scheduled_call_time || 'N/A'}</p>
            <div style="font-size: 0.85em; margin-top: 15px;">
                <span style="color: var(--accent-primary);">✓</span> Participating Members: ${p.users ? p.users.length : 0}
            </div>
            <button class="btn btn-secondary btn-small" style="margin-top: 15px;" onclick="selectProjectAndSwitch(${p.id})">Open Board</button>
        `;
        list.appendChild(div);
    });
}

function selectProjectAndSwitch(projectId) {
    projectSelector.value = projectId;
    currentProject = projects.find(p => p.id == projectId);
    updateProjectInfo();
    switchView('board');
    fetchTasks();
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
        let url = `${API_BASE}/tasks?user_id=${currentUser.id}&filter_type=${filterType}`;
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

// View Toggle Handlers
document.getElementById('btn-view-me').addEventListener('click', () => {
    filterType = 'me';
    document.getElementById('btn-view-me').classList.add('btn-primary');
    document.getElementById('btn-view-team').classList.remove('btn-primary');
    fetchTasks();
});

document.getElementById('btn-view-team').addEventListener('click', () => {
    filterType = 'team';
    document.getElementById('btn-view-team').classList.add('btn-primary');
    document.getElementById('btn-view-me').classList.remove('btn-primary');
    fetchTasks();
});

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
}function renderDashboard() {
    const statusCounts = { todo: 0, in_progress: 0, review: 0, done: 0 };
    const priorityCounts = { low: 0, medium: 0, high: 0 };
    const projectCounts = {};

    tasks.forEach(task => {
        if (statusCounts[task.status] !== undefined) statusCounts[task.status]++;
        if (priorityCounts[task.priority] !== undefined) priorityCounts[task.priority]++;
        
        const projName = task.project ? task.project.name : 'Unknown';
        projectCounts[projName] = (projectCounts[projName] || 0) + 1;
    });

    // Update Status Chart
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
        options: { plugins: { legend: { position: 'bottom', labels: { color: '#94a3b8' } } }, cutout: '70%' }
    });

    // Update Priority Chart
    const priorityCtx = document.getElementById('priorityChart').getContext('2d');
    if (priorityChartInstance) priorityChartInstance.destroy();
    priorityChartInstance = new Chart(priorityCtx, {
        type: 'bar',
        data: {
            labels: ['Low', 'Medium', 'High'],
            datasets: [{
                data: [priorityCounts.low, priorityCounts.medium, priorityCounts.high],
                backgroundColor: ['#3b82f6', '#eab308', '#ef4444'],
                borderRadius: 4
            }]
        },
        options: { 
            plugins: { legend: { display: false } },
            scales: { 
                y: { beginAtZero: true, grid: { color: '#334155' }, ticks: { color: '#94a3b8' } },
                x: { grid: { display: false }, ticks: { color: '#94a3b8' } }
            }
        }
    });
    
    // Update Project Chart
    const projectCtx = document.getElementById('projectChart').getContext('2d');
    if (projectChartInstance) projectChartInstance.destroy();
    projectChartInstance = new Chart(projectCtx, {
        type: 'polarArea',
        data: {
            labels: Object.keys(projectCounts),
            datasets: [{
                data: Object.values(projectCounts),
                backgroundColor: ['#6366f1', '#8b5cf6', '#ec4899', '#f43f5e', '#f97316'],
                borderWidth: 0
            }]
        },
        options: { 
            scales: { r: { grid: { color: '#334155' }, ticks: { display: false } } },
            plugins: { legend: { position: 'bottom', labels: { color: '#94a3b8' } } } 
        }
    });
    
    // Update Recent Activity (Comments)
    renderRecentActivity();
}

function renderRecentActivity() {
    const list = document.getElementById('recent-activity-list');
    list.innerHTML = '';
    
    // Flatten all comments from tasks
    let allComments = [];
    tasks.forEach(t => {
        if (t.comments) {
            t.comments.forEach(c => {
                allComments.push({ ...c, taskTitle: t.title });
            });
        }
    });
    
    // Sort by date (desc)
    allComments.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
    
    if (allComments.length === 0) {
        list.innerHTML = '<p style="color: var(--text-secondary); font-size: 0.9em;">No recent activity.</p>';
        return;
    }
    
    allComments.slice(0, 10).forEach(c => {
        const div = document.createElement('div');
        div.style.padding = '10px 0';
        div.style.borderBottom = '1px solid var(--border-color)';
        div.innerHTML = `
            <div style="font-size: 0.85em; font-weight: 600; color: var(--accent-primary);">${c.author}</div>
            <div style="font-size: 0.8em; margin: 2px 0;">${c.content}</div>
            <div style="font-size: 0.7em; color: var(--text-secondary);">on <span style="color: var(--text-primary);">${c.taskTitle}</span></div>
        `;
        list.appendChild(div);
    });
}

function createTaskCard(task) {
    const div = document.createElement('div');
    div.className = 'task-card';
    div.draggable = true;
    div.dataset.id = task.id;
    div.dataset.priority = task.priority;
    
    let blockedBadge = task.is_blocked ? '<span class="badge blocked">Blocked</span>' : '';
    
    const titleDiv = document.createElement('div');
    titleDiv.className = 'task-title';
    titleDiv.textContent = task.title;
    
    const metaDiv = document.createElement('div');
    metaDiv.className = 'task-meta';
    
    const assigneeDiv = document.createElement('div');
    assigneeDiv.className = 'task-assignee';
    assigneeDiv.innerHTML = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>';
    const nameSpan = document.createElement('span');
    nameSpan.textContent = task.assignee || 'Unassigned';
    assigneeDiv.appendChild(nameSpan);
    
    metaDiv.appendChild(assigneeDiv);
    if (task.is_blocked) {
        const blockedSpan = document.createElement('span');
        blockedSpan.className = 'badge blocked';
        blockedSpan.textContent = 'Blocked';
        metaDiv.appendChild(blockedSpan);
    }
    
    div.appendChild(titleDiv);
    div.appendChild(metaDiv);

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
newProjectBtn.addEventListener('click', () => {
    document.getElementById('project-id-field').value = '';
    document.getElementById('project-modal-title').textContent = 'Create Project';
    projectForm.reset();
    projectModal.classList.add('show');
});

closeProjectBtn.addEventListener('click', () => {
    projectModal.classList.remove('show');
});

projectForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const id = document.getElementById('project-id-field').value;
    const projectData = {
        name: document.getElementById('project-name').value,
        scheduled_call_time: document.getElementById('project-call-time').value,
    };
    
    const method = id ? 'PUT' : 'POST';
    const url = id ? `${API_BASE}/projects/${id}` : `${API_BASE}/projects`;
    
    try {
        await fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(projectData)
        });
        projectModal.classList.remove('show');
        await fetchProjects();
    } catch (err) {
        console.error('Project save failed', err);
    }
});

newTaskBtn.addEventListener('click', () => {
    document.getElementById('task-id').value = '';
    document.getElementById('modal-title').textContent = 'Create Task';
    taskForm.reset();
    if (currentProject) {
        document.getElementById('task-project-id').value = currentProject.id;
    }
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
    // Set assignee by user ID
    document.getElementById('task-assignee').value = task.assignee_id || '';
    document.getElementById('task-blocked').checked = task.is_blocked;
    document.getElementById('task-project-id').value = task.project_id || '';
    document.getElementById('task-form-error').style.display = 'none';
    
    renderComments(task.comments || []);
    commentsSection.style.display = 'block';
    document.getElementById('ai-summary-box').style.display = 'none';
    
    modal.classList.add('show');
}

taskForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const id = document.getElementById('task-id').value;
    const assigneeId = document.getElementById('task-assignee').value;
    // Find user by id to get their name
    const assigneeUser = users.find(u => u.id == assigneeId);
    
    const taskData = {
        title: document.getElementById('task-title').value.trim(),
        description: document.getElementById('task-desc').value.trim(),
        status: document.getElementById('task-status').value,
        priority: document.getElementById('task-priority').value,
        assignee: assigneeUser ? assigneeUser.name : null,
        assignee_id: assigneeId ? parseInt(assigneeId) : null,
        is_blocked: document.getElementById('task-blocked').checked,
        project_id: document.getElementById('task-project-id').value ? parseInt(document.getElementById('task-project-id').value) : null,
    };
    
    const method = id ? 'PUT' : 'POST';
    const url = id ? `${API_BASE}/tasks/${id}` : `${API_BASE}/tasks`;
    const errBox = document.getElementById('task-form-error');
    errBox.style.display = 'none';
    
    try {
        const res = await fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(taskData)
        });
        
        if (!res.ok) {
            const err = await res.json();
            errBox.textContent = err.detail || 'Failed to save task. Please try again.';
            errBox.style.display = 'block';
            return;
        }
        
        modal.classList.remove('show');
        await fetchTasks(); // await to ensure board updates
    } catch (err) {
        console.error('Save failed', err);
        errBox.textContent = 'Network error. Please check your connection.';
        errBox.style.display = 'block';
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

document.getElementById('nav-ai').addEventListener('click', async (e) => {
    e.preventDefault();
    switchView('ai');
    await fetchProjectInsights();
});

async function fetchProjectInsights() {
    if (!currentProject) {
        document.getElementById('ai-content').innerHTML = '<p>Please select a project from the header to see AI-generated insights.</p>';
        return;
    }
    
    loadingOverlay.style.display = 'flex';
    try {
        const res = await fetch(`${API_BASE}/ai/standup?project_id=${currentProject.id}`);
        const data = await res.json();
        
        let html = `<h3>Overview for ${currentProject.name}</h3>`;
        html += data.standup
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/\n\*/g, '<br>•')
            .replace(/\n/g, '<br>');
            
        document.getElementById('ai-content').innerHTML = html;
        document.getElementById('ai-query-response').style.display = 'none';
        document.getElementById('ai-query-input').value = '';
    } catch (err) {
        console.error('AI Insights Error', err);
    } finally {
        loadingOverlay.style.display = 'none';
    }
}

document.getElementById('btn-ai-query').addEventListener('click', async () => {
    const input = document.getElementById('ai-query-input');
    const prompt = input.value.trim();
    if (!prompt) return;
    
    loadingOverlay.style.display = 'flex';
    try {
        let url = `${API_BASE}/ai/query?user_id=${currentUser.id}`;
        if (currentProject) {
            url += `&project_id=${currentProject.id}`;
        }
        const res = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt })
        });
        const data = await res.json();
        
        const box = document.getElementById('ai-query-response');
        box.textContent = data.response;
        box.style.display = 'block';
    } catch (err) {
        console.error('AI Query Error', err);
    } finally {
        loadingOverlay.style.display = 'none';
    }
});

// Initial load
fetchUsers();
