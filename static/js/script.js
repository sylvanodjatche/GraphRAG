/**
 * UNIGRAPH — script.js
 * Logique du chatbot : envoi de questions, affichage des réponses,
 * visualisation du graphe, stats, gestion utilisateur.
 */

// ─────────────────────────────────────────────
//  Références DOM
// ─────────────────────────────────────────────
const chatWindow   = document.getElementById('chat-window');
const userInput    = document.getElementById('user-input');
const sendBtn      = document.getElementById('send-btn');
const welcomeScreen = document.getElementById('welcome-screen');

let network       = null;
let isAsking      = false;

// ─────────────────────────────────────────────
//  Init
// ─────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    loadStats();
    checkUserSession();
    setupSidebarSearch();
});

// ─────────────────────────────────────────────
//  Stats rapides (sidebar)
// ─────────────────────────────────────────────
async function loadStats() {
    try {
        const res  = await fetch('/api/stats');
        const data = await res.json();

        const byType = {};
        (data.nodes_by_type || []).forEach(r => { byType[r.type] = r.total; });

        setText('stat-dept', byType['Departement'] ?? '0');
        setText('stat-ens',  byType['Enseignant']  ?? '0');
        setText('stat-ue',   byType['UE']          ?? '0');
        setText('stat-etu',  byType['Etudiant']    ?? '0');
    } catch (_) {
        // silencieux si neo4j pas dispo
    }
}

function setText(id, val) {
    const el = document.getElementById(id);
    if (el) el.textContent = val;
}
// ─────────────────────────────────────────────
//  Vérification session et affichage du bouton Admin
// ─────────────────────────────────────────────
async function checkAdminAndShowLink() {
    try {
        const res = await fetch('/api/is_admin', { credentials: 'include' });
        const data = await res.json();
        const adminLink = document.getElementById('admin-link');
        if (adminLink && data.is_admin === true) {
            adminLink.style.display = 'flex';   // ou 'block' selon CSS
        } else if (adminLink) {
            adminLink.style.display = 'none';
        }
    } catch (err) {
        console.log("Erreur vérification admin", err);
    }
}

// Au chargement de la page, on lance également la vérification
document.addEventListener('DOMContentLoaded', () => {
    loadStats();
    checkAdminAndShowLink();   // ← nouvelle ligne
    setupSidebarSearch();
});

async function logout() {
    try {
        await fetch('/admin/logout', { method: 'POST', credentials: 'include' });
        window.location.reload();
    } catch (_) {}
}

// ─────────────────────────────────────────────
//  Sidebar search (filtre les suggestions)
// ─────────────────────────────────────────────
function setupSidebarSearch() {
    const input = document.getElementById('sidebar-search-input');
    if (!input) return;
    input.addEventListener('input', () => {
        const q = input.value.toLowerCase();
        document.querySelectorAll('.suggestion-chip').forEach(chip => {
            chip.style.display = chip.textContent.toLowerCase().includes(q) ? '' : 'none';
        });
    });
}

// ─────────────────────────────────────────────
//  Sidebar toggle (mobile)
// ─────────────────────────────────────────────
function toggleSidebar() {
    document.getElementById('sidebar').classList.toggle('open');
}

// ─────────────────────────────────────────────
//  Envoi d'une suggestion
// ─────────────────────────────────────────────
function askSuggestion(text) {
    userInput.value = text;
    askQuestion();
    // Ferme la sidebar en mobile
    document.getElementById('sidebar').classList.remove('open');
}

// ─────────────────────────────────────────────
//  Gestion clavier
// ─────────────────────────────────────────────
function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        askQuestion();
    }
}

// Auto-resize textarea
function autoResize(el) {
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 120) + 'px';
}

// ─────────────────────────────────────────────
//  Effacement du chat
// ─────────────────────────────────────────────
function clearChat() {
    chatWindow.innerHTML = '';
    // Remettre le welcome screen
    const ws = document.createElement('div');
    ws.className = 'welcome-screen';
    ws.id = 'welcome-screen';
    ws.innerHTML = `
        <div class="welcome-logo"><i class="fas fa-project-diagram"></i></div>
        <h2 class="welcome-title">Bonjour, je suis UNIGRAPH</h2>
        <p class="welcome-sub">
            Votre assistant académique intelligent pour la Faculté des Sciences.<br>
            Je réponds à vos questions sur les cours, enseignants, filières et départements.
        </p>
        <div class="welcome-chips">
            <button class="welcome-chip" onclick="askSuggestion('Qui dirige le département Informatique ?')">
                <i class="fas fa-crown"></i> Chef du département
            </button>
            <button class="welcome-chip" onclick="askSuggestion('Quels cours sont en M1 Informatique ?')">
                <i class="fas fa-book"></i> Cours M1
            </button>
            <button class="welcome-chip" onclick="askSuggestion('Quelles filières existent ?')">
                <i class="fas fa-sitemap"></i> Filières
            </button>
            <button class="welcome-chip" onclick="askSuggestion('Quelles spécialités en L3 ?')">
                <i class="fas fa-flask"></i> Spécialités L3
            </button>
        </div>
    `;
    chatWindow.appendChild(ws);
}

// ─────────────────────────────────────────────
//  ENVOI D'UNE QUESTION (cœur du chatbot)
// ─────────────────────────────────────────────
async function askQuestion() {
    const question = userInput.value.trim();
    if (!question || isAsking) return;

    isAsking = true;
    sendBtn.disabled = true;

    // Cacher le welcome screen au premier message
    const ws = document.getElementById('welcome-screen');
    if (ws) ws.remove();

    // ── Bulle utilisateur ──
    appendMessage('user', question);

    userInput.value = '';
    userInput.style.height = 'auto';

    // ── Bulle "en train de réfléchir" ──
    const thinkingId = 'thinking-' + Date.now();
    appendThinking(thinkingId);

    try {
        const res  = await fetch('/ask', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ question })
        });
        const data = await res.json();

        // Supprimer le thinking
        const thinkingEl = document.getElementById(thinkingId);
        if (thinkingEl) thinkingEl.remove();

        if (data.answer) {
            appendAIMessage(data.answer, data.debug_query);
        } else if (data.error) {
            appendAIMessage(
                `❌ Une erreur est survenue lors du traitement de votre question.\n\n*Détail :* ${data.error}`,
                data.attempted_query
            );
        }

    } catch (err) {
        const thinkingEl = document.getElementById(thinkingId);
        if (thinkingEl) thinkingEl.remove();
        appendAIMessage('❌ Impossible de contacter le serveur. Vérifiez que Flask est bien démarré.');
        console.error('Erreur réseau :', err);
    }

    isAsking = false;
    sendBtn.disabled = false;
    userInput.focus();
}

// ─────────────────────────────────────────────
//  Helpers d'affichage des messages
// ─────────────────────────────────────────────
function appendMessage(role, text) {
    const row = document.createElement('div');
    row.className = `message-row ${role === 'user' ? 'user-row' : ''}`;

    const avatarHtml = role === 'user'
        ? `<div class="avatar avatar-user"><i class="fas fa-user"></i></div>`
        : `<div class="avatar avatar-ai"><i class="fas fa-robot"></i></div>`;

    const bubbleClass = role === 'user' ? 'bubble-user' : 'bubble-ai';
    const safeText = escapeHtml(text).replace(/\n/g, '<br>');

    row.innerHTML = `
        ${avatarHtml}
        <div class="bubble ${bubbleClass}">${safeText}</div>
    `;
    chatWindow.appendChild(row);
    scrollToBottom();
}

function appendThinking(id) {
    const row = document.createElement('div');
    row.className = 'message-row';
    row.id = id;
    row.innerHTML = `
        <div class="avatar avatar-ai"><i class="fas fa-robot"></i></div>
        <div class="bubble bubble-ai">
            <div class="thinking-dots">
                <span></span><span></span><span></span>
            </div>
        </div>
    `;
    chatWindow.appendChild(row);
    scrollToBottom();
}

function appendAIMessage(text, debugQuery = null) {
    const row = document.createElement('div');
    row.className = 'message-row';

    const debugId = 'debug-' + Date.now();
    
    let escapedText = escapeHtml(text);
    
    // Remplacer toutes les URLs par une icône appareil photo cliquable
    const urlRegex = /(https?:\/\/[^\s]+)/g;
    let linkedText = escapedText.replace(urlRegex, function(url) {
        // Retourne une icône 📷 cliquable (peu importe le type d'URL)
        return `<a href="${url}" target="_blank" rel="noopener noreferrer" style="color:#60a5fa; text-decoration:none; font-size:1.2rem;">📷</a>`;
    });
    
    const formattedText = linkedText.replace(/\n/g, '<br>');

    let debugHtml = '';
    if (debugQuery) {
        debugHtml = `
            <div class="debug-toggle">
                <button class="debug-btn" onclick="toggleDebug('${debugId}')">
                    <i class="fas fa-code"></i> Requête Cypher générée
                </button>
                <pre class="debug-content" id="${debugId}">${escapeHtml(debugQuery)}</pre>
            </div>
        `;
    }

    row.innerHTML = `
        <div class="avatar avatar-ai"><i class="fas fa-robot"></i></div>
        <div class="bubble bubble-ai">
            <div>${formattedText}</div>
            ${debugHtml}
        </div>
    `;
    chatWindow.appendChild(row);
    scrollToBottom();
}
function toggleDebug(id) {
    const el = document.getElementById(id);
    if (el) el.classList.toggle('open');
}

function scrollToBottom() {
    chatWindow.scrollTop = chatWindow.scrollHeight;
}

function escapeHtml(str) {
    if (typeof str !== 'string') return String(str);
    return str
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

// ─────────────────────────────────────────────
//  VISUALISATION DU GRAPHE
// ─────────────────────────────────────────────
function toggleGraph() {
    const overlay = document.getElementById('graph-overlay');
    if (overlay.classList.contains('hidden')) {
        overlay.classList.remove('hidden');
        loadGraph();
    } else {
        overlay.classList.add('hidden');
    }
}

async function loadGraph() {
    const container = document.getElementById('mynetwork');
    container.innerHTML = '<p style="color:#64748b;text-align:center;padding:60px;font-size:14px;">Chargement du graphe...</p>';

    try {
        const res  = await fetch('/graph-data');
        const data = await res.json();

        // Mettre à jour le compteur
        const countEl = document.getElementById('graph-node-count');
        if (countEl) countEl.textContent = `${data.nodes.length} nœuds · ${data.edges.length} relations`;

        container.innerHTML = '';

        const colorMap = {
            'Enseignant':  { background: '#60a5fa', border: '#2563eb' },
            'UE':          { background: '#f87171', border: '#dc2626' },
            'Etudiant':    { background: '#fbbf24', border: '#d97706' },
            'Departement': { background: '#34d399', border: '#059669' },
            'Filiere':     { background: '#a78bfa', border: '#7c3aed' },
            'Niveau':      { background: '#fb923c', border: '#ea580c' },
            'Specialite':  { background: '#e879f9', border: '#a21caf' },
            'TypeCours':   { background: '#38bdf8', border: '#0284c7' },
            'Secretaire':  { background: '#94a3b8', border: '#475569' },
        };

        const visNodes = data.nodes.map(n => ({
            id:    n.id,
            label: n.label,
            color: colorMap[n.group] || { background: '#475569', border: '#334155' },
            font:  { color: '#ffffff', size: 11, face: 'Space Grotesk' },
            size:  16,
            shape: 'dot',
        }));

        const visEdges = data.edges.map(e => ({
            from:   e.from,
            to:     e.to,
            label:  e.label,
            color:  { color: '#334155', highlight: '#3b82f6' },
            font:   { color: '#64748b', size: 9, face: 'JetBrains Mono' },
            arrows: { to: { enabled: true, scaleFactor: 0.6 } },
        }));

        const options = {
            nodes: { shape: 'dot', size: 16 },
            edges: { smooth: { type: 'continuous' } },
            physics: {
                stabilization: { iterations: 120 },
                barnesHut: { gravitationalConstant: -8000, springLength: 120 }
            },
            interaction: { hover: true, tooltipDelay: 200 },
            background: { color: '#050b18' }
        };

        if (network !== null) { network.destroy(); }
        network = new vis.Network(container, { nodes: visNodes, edges: visEdges }, options);

    } catch (err) {
        container.innerHTML = `<p style="color:#f87171;text-align:center;padding:60px;font-size:14px;">Erreur de chargement du graphe : ${err.message}</p>`;
    }
}

// ─────────────────────────────────────────────
//  Vérification session et affichage du bouton Admin
// ─────────────────────────────────────────────
async function checkAdminAndShowLink() {
    try {
        const res = await fetch('/api/is_admin', { credentials: 'include' });
        const data = await res.json();
        const adminLink = document.getElementById('admin-link');
        const adminLinkText = document.getElementById('admin-link-text');
        if (adminLink) {
            if (data.is_admin === true) {
                // Connecté en tant qu'admin
                adminLink.href = '/admin';
                adminLinkText.textContent = 'Administration';
                adminLink.style.display = 'flex';
            } else {
                // Non connecté ou non admin : afficher le lien vers la page de login
                adminLink.href = '/admin/login';
                adminLinkText.textContent = 'Connexion admin';
                adminLink.style.display = 'flex';
            }
        }
    } catch (err) {
        console.log("Erreur vérification admin", err);
        // En cas d'erreur, on cache quand même le lien (ou on affiche connexion)
        const adminLink = document.getElementById('admin-link');
        if (adminLink) adminLink.style.display = 'none';
    }
}

async function logout() {
    try {
        await fetch('/admin/logout', { method: 'POST', credentials: 'include' });
        window.location.reload();  // le rechargement rappelle checkAdminAndShowLink()
    } catch (_) {}
}