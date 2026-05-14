/**
 * EduAI Platform — Client-Side Application Logic
 */

const API = 'https://onlineeducationplatform.up.railway.app';
let currentUser = null;
let currentConvId = null;
let assignConvId = null;
let techConvId = null;

// ── Auth ──
async function handleLogin() {
    const username = document.getElementById('login-username').value.trim();
    const password = document.getElementById('login-password').value.trim();
    const errEl = document.getElementById('login-error');
    errEl.textContent = '';

    if (!username || !password) { errEl.textContent = 'Please fill in all fields'; return; }

    try {
        const res = await fetch(`${API}/api/auth/login`, {
            method: 'POST', headers: {'Content-Type':'application/json'},
            body: JSON.stringify({username, password}), credentials: 'include'
        });
        const data = await res.json();
        if (!res.ok) { errEl.textContent = data.error; return; }
        currentUser = data.user;
        showApp();
    } catch(e) { errEl.textContent = 'Connection error. Is the server running?'; }
}

async function handleRegister() {
    const name = document.getElementById('reg-name').value.trim();
    const email = document.getElementById('reg-email').value.trim();
    const username = document.getElementById('reg-username').value.trim();
    const password = document.getElementById('reg-password').value.trim();
    const errEl = document.getElementById('register-error');
    errEl.textContent = '';

    if (!name || !username || !password) { errEl.textContent = 'Please fill required fields'; return; }

    try {
        const res = await fetch(`${API}/api/auth/register`, {
            method: 'POST', headers: {'Content-Type':'application/json'},
            body: JSON.stringify({display_name:name, email, username, password}), credentials: 'include'
        });
        const data = await res.json();
        if (!res.ok) { errEl.textContent = data.error; return; }
        showToast('Account created! Please login.', 'success');
        toggleAuthForm();
    } catch(e) { errEl.textContent = 'Connection error'; }
}

async function handleLogout() {
    await fetch(`${API}/api/auth/logout`, {method:'POST', credentials:'include'});
    currentUser = null;
    document.getElementById('app-shell').classList.add('hidden');
    document.getElementById('login-view').classList.remove('hidden');
}

function toggleAuthForm() {
    document.getElementById('login-form').classList.toggle('hidden');
    document.getElementById('register-form').classList.toggle('hidden');
}

// ── App Shell ──
function showApp() {
    document.getElementById('login-view').classList.add('hidden');
    document.getElementById('app-shell').classList.remove('hidden');
    document.getElementById('greeting-name').textContent = currentUser.username;
    document.getElementById('user-display-name').textContent = currentUser.display_name;
    document.getElementById('user-role-label').textContent = currentUser.role;
    document.getElementById('user-avatar').textContent = currentUser.display_name[0].toUpperCase();

    if (currentUser.role === 'admin' || currentUser.role === 'faculty') {
        document.getElementById('admin-nav').classList.remove('hidden');
    }
    loadConversations();
}

// ── Navigation ──
function navigateTo(view) {
    document.querySelectorAll('.view-panel').forEach(v => v.classList.add('hidden'));
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));

    const panel = document.getElementById(`view-${view}`);
    if (panel) panel.classList.remove('hidden');

    const navBtn = document.querySelector(`.nav-item[data-view="${view}"]`);
    if (navBtn) navBtn.classList.add('active');

    if (view === 'tickets') loadTickets();
    if (view === 'admin') loadAdminStats();
    if (view === 'dashboard') loadConversations();
}

// ── Chat ──
function handleChatKey(e) { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); } }
function handleAssignmentKey(e) { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendAssignmentMessage(); } }
function handleTechKey(e) { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendTechMessage(); } }

function sendQuickMessage(text) {
    document.getElementById('chat-input').value = text;
    sendMessage();
}

async function sendMessage() {
    const input = document.getElementById('chat-input');
    const msg = input.value.trim();
    if (!msg) return;

    input.value = '';
    const container = document.getElementById('chat-messages');
    appendMessage(container, msg, 'user');
    showTyping(container);

    try {
        const res = await fetch(`${API}/api/chat`, {
            method:'POST', headers:{'Content-Type':'application/json'},
            body: JSON.stringify({message: msg, conversation_id: currentConvId}),
            credentials:'include'
        });
        const data = await res.json();
        removeTyping(container);

        if (!res.ok) { appendMessage(container, data.error || 'Error occurred', 'assistant'); return; }

        currentConvId = data.conversation_id;
        appendMessage(container, data.response, 'assistant', data.agent_type);
        updateAgentBadge(data.agent_type);

        if (data.guardrail_triggered) showToast('⚠️ Guardrail activated', 'error');
        if (data.escalated) showToast('📋 Escalated to human support', 'success');
    } catch(e) {
        removeTyping(container);
        appendMessage(container, 'Connection error. Please try again.', 'assistant');
    }
}

function sendAssignmentMsg(text) {
    document.getElementById('assignment-input').value = text;
    sendAssignmentMessage();
}

async function sendAssignmentMessage() {
    const input = document.getElementById('assignment-input');
    const msg = input.value.trim();
    if (!msg) return;
    input.value = '';
    const container = document.getElementById('assignment-messages');
    appendMessage(container, msg, 'user');
    showTyping(container);

    try {
        const res = await fetch(`${API}/api/chat`, {
            method:'POST', headers:{'Content-Type':'application/json'},
            body: JSON.stringify({message: msg, conversation_id: assignConvId}),
            credentials:'include'
        });
        const data = await res.json();
        removeTyping(container);
        if (res.ok) { assignConvId = data.conversation_id; appendMessage(container, data.response, 'assistant', data.agent_type); }
        else appendMessage(container, data.error, 'assistant');
    } catch(e) { removeTyping(container); appendMessage(container, 'Connection error.', 'assistant'); }
}

function sendTechMsg(text) {
    document.getElementById('tech-input').value = text;
    sendTechMessage();
}

async function sendTechMessage() {
    const input = document.getElementById('tech-input');
    const msg = input.value.trim();
    if (!msg) return;
    input.value = '';
    const container = document.getElementById('tech-messages');
    appendMessage(container, msg, 'user');
    showTyping(container);

    try {
        const res = await fetch(`${API}/api/chat`, {
            method:'POST', headers:{'Content-Type':'application/json'},
            body: JSON.stringify({message: msg, conversation_id: techConvId}),
            credentials:'include'
        });
        const data = await res.json();
        removeTyping(container);
        if (res.ok) { techConvId = data.conversation_id; appendMessage(container, data.response, 'assistant', data.agent_type); }
        else appendMessage(container, data.error, 'assistant');
    } catch(e) { removeTyping(container); appendMessage(container, 'Connection error.', 'assistant'); }
}

function startNewChat() {
    currentConvId = null;
    const container = document.getElementById('chat-messages');
    container.innerHTML = `<div class="message message-assistant">👋 New conversation started! How can I help you?</div>`;
    document.getElementById('chat-quick-actions').classList.remove('hidden');
}

// ── Message Rendering ──
function appendMessage(container, text, role, agentType) {
    const div = document.createElement('div');
    div.className = `message message-${role}`;
    div.innerHTML = role === 'assistant' ? renderMarkdown(text) : escapeHtml(text);
    if (agentType && role === 'assistant') {
        const meta = document.createElement('div');
        meta.className = 'message-meta';
        meta.textContent = `Agent: ${agentType}`;
        div.appendChild(meta);
    }
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;

    // Hide quick actions after first message
    const qa = container.parentElement.querySelector('.quick-actions');
    if (qa && role === 'user') qa.classList.add('hidden');
}

function showTyping(container) {
    const div = document.createElement('div');
    div.className = 'typing-indicator';
    div.id = 'typing-' + container.id;
    div.innerHTML = '<span></span><span></span><span></span>';
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

function removeTyping(container) {
    const el = document.getElementById('typing-' + container.id);
    if (el) el.remove();
}

function updateAgentBadge(type) {
    const badge = document.getElementById('chat-agent-type');
    const labels = {course:'Course Guide', assignment:'Assignment Help', technical:'Tech Support', escalation:'Escalation'};
    badge.textContent = labels[type] || type;
    badge.className = 'chat-agent-badge badge-' + (type || 'course');
}

// ── Markdown Renderer (simple) ──
function renderMarkdown(text) {
    if (!text) return '';
    let html = escapeHtml(text);
    // Code blocks
    html = html.replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>');
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
    // Bold & italic
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');
    // Headers
    html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
    html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>');
    html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>');
    // Lists
    html = html.replace(/^- (.+)$/gm, '<li>$1</li>');
    html = html.replace(/^(\d+)\. (.+)$/gm, '<li>$2</li>');
    html = html.replace(/((<li>.*<\/li>\n?)+)/g, '<ul>$1</ul>');
    // Line breaks
    html = html.replace(/\n/g, '<br>');
    return html;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ── Conversations ──
async function loadConversations() {
    try {
        const res = await fetch(`${API}/api/conversations`, {credentials:'include'});
        if (!res.ok) return;
        const data = await res.json();
        const el = document.getElementById('recent-convs');
        if (!data.conversations || data.conversations.length === 0) {
            el.innerHTML = '<p style="color:var(--text-muted); font-size:14px;">No recent conversations yet.</p>';
            return;
        }
        el.innerHTML = data.conversations.slice(0, 5).map(c => `
            <div class="conv-item" onclick="loadConversation(${c.id})">
                <div>
                    <div class="conv-title">${escapeHtml(c.title || 'Conversation')}</div>
                    <div class="conv-time">${c.agent_type} • ${timeAgo(c.updated_at)}</div>
                </div>
                <span class="badge badge-${c.status}">${c.status}</span>
            </div>
        `).join('');
    } catch(e) {}
}

async function loadConversation(id) {
    currentConvId = id;
    navigateTo('chat');
    try {
        const res = await fetch(`${API}/api/conversations/${id}/messages`, {credentials:'include'});
        const data = await res.json();
        const container = document.getElementById('chat-messages');
        container.innerHTML = '';
        (data.messages || []).forEach(m => appendMessage(container, m.content, m.role, m.agent_type));
    } catch(e) {}
}

// ── Tickets ──
async function loadTickets() {
    try {
        const res = await fetch(`${API}/api/tickets`, {credentials:'include'});
        const data = await res.json();
        const tbody = document.getElementById('tickets-body');
        if (!data.tickets || data.tickets.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;padding:24px;color:var(--text-muted)">No tickets yet</td></tr>';
            return;
        }
        tbody.innerHTML = data.tickets.map(t => `
            <tr>
                <td>#${t.id}</td>
                <td>${t.category}</td>
                <td>${escapeHtml(t.subject)}</td>
                <td><span class="badge badge-${t.status}">${t.status}</span></td>
                <td><span class="badge badge-${t.priority}">${t.priority}</span></td>
                <td>${timeAgo(t.created_at)}</td>
            </tr>
        `).join('');
    } catch(e) {}
}

async function createTicket() {
    const category = document.getElementById('ticket-category').value;
    const subject = document.getElementById('ticket-subject').value.trim();
    const description = document.getElementById('ticket-desc').value.trim();
    if (!subject) { showToast('Subject is required', 'error'); return; }

    try {
        const res = await fetch(`${API}/api/tickets`, {
            method:'POST', headers:{'Content-Type':'application/json'},
            body: JSON.stringify({category, subject, description}), credentials:'include'
        });
        if (res.ok) {
            showToast('Ticket created!', 'success');
            document.getElementById('ticket-subject').value = '';
            document.getElementById('ticket-desc').value = '';
            loadTickets();
        }
    } catch(e) { showToast('Error creating ticket', 'error'); }
}

// ── Escalation ──
async function requestEscalation() {
    const reason = document.getElementById('esc-reason').value;
    const summary = document.getElementById('esc-summary').value.trim();

    try {
        const res = await fetch(`${API}/api/escalate`, {
            method:'POST', headers:{'Content-Type':'application/json'},
            body: JSON.stringify({reason, summary, conversation_id: currentConvId}), credentials:'include'
        });
        if (res.ok) {
            document.getElementById('esc-status').classList.remove('hidden');
            showToast('Escalation submitted!', 'success');
        }
    } catch(e) { showToast('Error submitting escalation', 'error'); }
}

// ── Admin Dashboard ──
async function loadAdminStats() {
    try {
        const res = await fetch(`${API}/api/admin/stats`, {credentials:'include'});
        if (!res.ok) return;
        const stats = await res.json();

        // Stat cards
        document.getElementById('admin-stats').innerHTML = [
            {label:'Total Queries', value: stats.total_queries, icon:'📊'},
            {label:'Avg Response', value: stats.avg_response_time_ms+'ms', icon:'⏱️'},
            {label:'Escalation Rate', value: stats.escalation_rate+'%', icon:'📈'},
            {label:'Violations', value: stats.total_violations, icon:'🛡️'},
            {label:'Open Tickets', value: stats.open_tickets, icon:'🎫'},
            {label:'Students', value: stats.total_students, icon:'👨‍🎓'},
            {label:'Satisfaction', value: Math.round(stats.satisfaction_score)+'%', icon:'😊'},
            {label:'Resolved', value: stats.resolved_tickets, icon:'✅'},
        ].map(s => `
            <div class="stat-card glass">
                <div style="font-size:24px;margin-bottom:8px">${s.icon}</div>
                <div class="stat-value">${s.value}</div>
                <div class="stat-label">${s.label}</div>
            </div>
        `).join('');

        // Agent chart
        const agents = stats.queries_by_agent || {};
        const maxAgent = Math.max(...Object.values(agents), 1);
        const colors = {course:'var(--accent-purple)', assignment:'var(--accent-teal)', technical:'var(--accent-blue)', escalation:'var(--accent-rose)'};
        document.getElementById('chart-agents').innerHTML = Object.entries(agents).map(([k,v]) => `
            <div class="chart-bar">
                <div class="chart-bar-value">${v}</div>
                <div class="chart-bar-fill" style="height:${(v/maxAgent)*160}px; background:${colors[k]||'var(--accent-purple)'}"></div>
                <div class="chart-bar-label">${k}</div>
            </div>
        `).join('') || '<p style="color:var(--text-muted);font-size:13px">No data yet</p>';

        // Response time chart
        const trend = (stats.response_time_trend || []).reverse();
        const maxTime = Math.max(...trend.map(t => t.avg_time || 0), 1);
        document.getElementById('chart-response').innerHTML = trend.map(t => `
            <div class="chart-bar">
                <div class="chart-bar-value">${Math.round(t.avg_time||0)}</div>
                <div class="chart-bar-fill" style="height:${((t.avg_time||0)/maxTime)*160}px; background:linear-gradient(to top, var(--accent-teal), var(--accent-purple))"></div>
                <div class="chart-bar-label">${(t.date||'').slice(5)}</div>
            </div>
        `).join('') || '<p style="color:var(--text-muted);font-size:13px">No data yet</p>';

        // Violations table
        const vBody = document.getElementById('violations-body');
        vBody.innerHTML = (stats.recent_violations || []).map(v => `
            <tr>
                <td><span class="badge badge-high">${v.violation_type}</span></td>
                <td>${escapeHtml((v.original_query||'').slice(0,60))}</td>
                <td>${v.action_taken}</td>
                <td><span class="badge badge-${v.severity}">${v.severity}</span></td>
                <td>${timeAgo(v.created_at)}</td>
            </tr>
        `).join('') || '<tr><td colspan="5" style="text-align:center;padding:16px;color:var(--text-muted)">No violations</td></tr>';

        // Escalations table
        const eRes = await fetch(`${API}/api/admin/escalations`, {credentials:'include'});
        if (eRes.ok) {
            const eData = await eRes.json();
            document.getElementById('escalations-body').innerHTML = (eData.escalations || []).map(e => `
                <tr>
                    <td>${escapeHtml(e.display_name||'Unknown')}</td>
                    <td>${e.reason}</td>
                    <td>${escapeHtml((e.summary||'').slice(0,60))}</td>
                    <td><span class="badge badge-${e.priority}">${e.priority}</span></td>
                    <td><span class="badge badge-${e.status}">${e.status}</span></td>
                </tr>
            `).join('') || '<tr><td colspan="5" style="text-align:center;padding:16px;color:var(--text-muted)">No escalations</td></tr>';
        }
    } catch(e) { console.error('Admin stats error:', e); }
}

// ── Utils ──
function timeAgo(dateStr) {
    if (!dateStr) return '';
    const diff = Date.now() - new Date(dateStr).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'just now';
    if (mins < 60) return mins + 'm ago';
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return hrs + 'h ago';
    return Math.floor(hrs / 24) + 'd ago';
}

function showToast(msg, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = msg;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3500);
}

// ── Init (check session) ──
(async function init() {
    try {
        const res = await fetch(`${API}/api/auth/me`, {credentials:'include'});
        if (res.ok) {
            const data = await res.json();
            if (data.authenticated) { currentUser = data.user; showApp(); }
        }
    } catch(e) {}

    // Enter key login
    document.getElementById('login-password').addEventListener('keydown', e => {
        if (e.key === 'Enter') handleLogin();
    });
})();
