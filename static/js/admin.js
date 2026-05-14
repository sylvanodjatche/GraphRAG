/**
 * UNIGRAPH — admin.js
 * Logique du panneau d'administration.
 * Appelle toutes les routes /admin/api/* protégées par JWT.
 */

// ─────────────────────────────────────────────
//  Init au chargement
// ─────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    loadUserInfo();
    loadDashboardStats();
    loadClusterInfo();
});

// ─────────────────────────────────────────────
//  Infos utilisateur connecté
// ─────────────────────────────────────────────
async function loadUserInfo() {
    try {
        const res  = await fetch('/api/me', { credentials: 'include' });
        const data = await res.json();
        if (data.authenticated && data.user) {
            const u = data.user;
            const nameEl  = document.getElementById('user-name');
            const emailEl = document.getElementById('user-email');
            if (nameEl)  nameEl.textContent  = u.name  || 'Administrateur';
            if (emailEl) emailEl.textContent = u.email || '';
        }
    } catch (_) {}
}

// ─────────────────────────────────────────────
//  Déconnexion
// ─────────────────────────────────────────────
async function handleLogout() {
    try {
        await fetch('/admin/logout', { method: 'POST', credentials: 'include' });
    } catch (_) {}
    window.location.href = '/admin/login?logout=1';
}

// ─────────────────────────────────────────────
//  Navigation entre panels
// ─────────────────────────────────────────────
function showPanel(name) {
    // Cacher tous les panels
    document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
    // Désactiver tous les nav-items
    document.querySelectorAll('.nav-item').forEach(b => b.classList.remove('active'));

    // Activer le panel cible
    const panel = document.getElementById('panel-' + name);
    if (panel) panel.classList.add('active');

    // Activer le bouton correspondant
    document.querySelectorAll('.nav-item').forEach(b => {
        if (b.getAttribute('onclick') === `showPanel('${name}')`) {
            b.classList.add('active');
        }
    });

    // Breadcrumb
    const icons = {
        dashboard:   'fa-chart-pie',
        cluster:     'fa-server',
        enseignants: 'fa-chalkboard-teacher',
        departements:'fa-university',
        filieres:    'fa-code-branch',
        ue:          'fa-book-open',
        etudiants:   'fa-user-graduate',
        liaisons:    'fa-link',
        database:    'fa-database',
    };
    const labels = {
        dashboard:   'Vue d\'ensemble',
        cluster:     'Cluster Neo4j',
        enseignants: 'Enseignants',
        departements:'Départements',
        filieres:    'Filières',
        ue:          'Unités d\'enseignement',
        etudiants:   'Étudiants',
        liaisons:    'Liaisons',
        database:    'Base de données',
    };
    const bc = document.getElementById('breadcrumb');
    if (bc) {
        bc.innerHTML = `<i class="fas ${icons[name] || 'fa-circle'} mr-2 text-blue-400"></i>${labels[name] || name}`;
    }

    // Actions spécifiques par panel
    if (name === 'enseignants') loadEnseignants();
    if (name === 'dashboard')  loadDashboardStats();
    if (name === 'cluster')    loadClusterInfo();
    if (name === 'secretaires') loadSecretaires();
    if (name === 'delegues') loadDelegues();
    if (name === 'etudiants') loadEtudiants();
    if (name === 'filieres') loadFilieres();
    if (name === 'departements') loadDepartements();
    if (name === 'ue') loadUEs();   // ← Nouvelle ligne
    if (name === 'relations') {
        loadEnseigneRelations();
        loadChefsDepartement();
        loadSpecialites();
    }
}
 
// ─────────────────────────────────────────────
//  Dashboard : stats des nœuds
// ─────────────────────────────────────────────
async function loadDashboardStats() {
    try {
        const res  = await fetch('/admin/api/stats', { credentials: 'include' });
        if (res.status === 401 || res.status === 403) return;
        const data = await res.json();

        const byType = {};
        (data.nodes || []).forEach(r => { byType[r.type] = r.total; });

        setText('stat-enseignant', byType['Enseignant'] ?? '—');
        setText('stat-ue',         byType['UE']         ?? '—');
        setText('stat-etudiant',   byType['Etudiant']   ?? '—');
        const total = (data.nodes || []).reduce((s, r) => s + r.total, 0);
        setText('stat-total', total || '—');

        // Breakdown graphique
        const breakdown = document.getElementById('nodes-breakdown');
        if (breakdown && data.nodes) {
            breakdown.innerHTML = data.nodes.map(r => `
                <div class="flex items-center gap-3">
                    <span class="text-xs text-slate-400 w-28 shrink-0">${r.type || 'Inconnu'}</span>
                    <div class="flex-1 bg-slate-900 rounded-full h-2 overflow-hidden">
                        <div class="h-full rounded-full" style="
                            width: ${Math.min(100, (r.total / Math.max(...data.nodes.map(x=>x.total))) * 100)}%;
                            background: linear-gradient(90deg, #3b82f6, #6366f1);
                        "></div>
                    </div>
                    <span class="text-sm font-bold text-blue-400 w-8 text-right">${r.total}</span>
                </div>
            `).join('');
        }

    } catch (err) {
        console.error('Stats error:', err);
    }
}

// ─────────────────────────────────────────────
//  Cluster Neo4j
// ─────────────────────────────────────────────
async function loadClusterInfo() {
    try {
        const res  = await fetch('/admin/api/cluster', { credentials: 'include' });
        if (res.status === 401 || res.status === 403) return;
        const data = await res.json();

        const dotEl   = document.getElementById('cluster-dot');
        const textEl  = document.getElementById('cluster-status-text');
        const details = document.getElementById('cluster-details');

        if (data.status === 'ok') {
            if (dotEl)  { dotEl.className = 'status-dot dot-green'; }
            if (textEl) { textEl.textContent = `${data.servers.length} nœuds actifs`; }
            if (details) {
                details.innerHTML = `
                    <h3 class="text-sm font-semibold text-blue-300 mb-3 flex items-center gap-2">
                        <i class="fas fa-info-circle"></i> Informations cluster
                    </h3>
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>ID</th><th>Adresses</th><th>Rôle</th><th>Base</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${data.servers.map(s => `
                                <tr>
                                    <td><code>${(s.id || '').slice(0,8)}…</code></td>
                                    <td>${(s.addresses || []).join(', ')}</td>
                                    <td><span class="text-${s.role === 'LEADER' ? 'green' : 'blue'}-400">${s.role}</span></td>
                                    <td>${s.database || '—'}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                `;
            }
            // Marquer les nœuds 2 et 3 comme en ligne
            setNodeStatus('node2-status', true);
            setNodeStatus('node3-status', data.servers.length >= 3);

        } else {
            // Mode standalone (Neo4j Community)
            if (dotEl)  { dotEl.className = 'status-dot'; dotEl.style.background = '#fbbf24'; }
            if (textEl) { textEl.textContent = 'Standalone (Community)'; }
            if (details) {
                details.innerHTML = `
                    <h3 class="text-sm font-semibold text-blue-300 mb-3 flex items-center gap-2">
                        <i class="fas fa-info-circle"></i> Mode standalone
                    </h3>
                    <p class="text-slate-400 text-sm">
                        <i class="fas fa-info-circle text-amber-400 mr-2"></i>
                        Neo4j Community Edition est en cours d'utilisation. 
                        Le clustering nécessite Neo4j Enterprise (docker-compose.yml fourni).
                    </p>
                    <p class="text-slate-500 text-xs mt-2">${data.message}</p>
                `;
            }
        }
    } catch (err) {
        console.error('Cluster error:', err);
    }
}

function setNodeStatus(id, online) {
    const el = document.getElementById(id);
    if (!el) return;
    if (online) {
        el.innerHTML = `<span class="status-dot dot-green"></span><span class="text-xs text-green-400">En ligne</span>`;
    } else {
        el.innerHTML = `<span class="status-dot dot-red"></span><span class="text-xs text-red-400">Hors ligne</span>`;
    }
}

// ─────────────────────────────────────────────
//  Charger la liste des enseignants
// ─────────────────────────────────────────────
async function loadEnseignants() {
    const listEl = document.getElementById('enseignants-list');
    if (!listEl) return;
    listEl.innerHTML = '<p class="text-slate-500 text-sm">Chargement...</p>';

    try {
        const res  = await fetch('/admin/api/nodes/Enseignant', { credentials: 'include' });
        const data = await res.json();

        if (!Array.isArray(data) || data.length === 0) {
            listEl.innerHTML = '<p class="text-slate-500 text-sm italic">Aucun enseignant enregistré.</p>';
            return;
        }

        listEl.innerHTML = `
            <table class="data-table">
                <thead>
                    <tr><th>Titre</th><th>Nom</th><th>Grade</th><th>Email</th></tr>
                </thead>
                <tbody>
                    ${data.map(row => {
                        const e = row.n || row;
                        return `
                            <tr>
                                <td>${e.titre || '—'}</td>
                                <td class="font-medium text-slate-200">${e.nom || '—'}</td>
                                <td>${e.grade || '—'}</td>
                                <td><code>${e.email || '—'}</code></td>
                            </tr>
                        `;
                    }).join('')}
                </tbody>
            </table>
        `;
    } catch (err) {
        listEl.innerHTML = `<p class="text-red-400 text-sm">Erreur : ${err.message}</p>`;
    }
}

// ─────────────────────────────────────────────
//  Ajouter un enseignant
// ─────────────────────────────────────────────
async function addEnseignant() {
    const payload = {
        nom:       getVal('ens-nom'),
        prenom:    getVal('ens-prenom'),
        titre:     getVal('ens-titre'),
        grade:     getVal('ens-grade'),
        email:     getVal('ens-email'),
        photo_url: getVal('ens-photo'),
    };

    if (!payload.nom || !payload.prenom || !payload.email) {
        showToast('Nom, prénom et email sont obligatoires.', 'error');
        return;
    }

    await apiCall('POST', '/admin/api/enseignant', payload, () => {
        clearFields(['ens-nom','ens-prenom','ens-grade','ens-email','ens-photo']);
        loadEnseignants();
    });
}

// ─────────────────────────────────────────────
//  Ajouter un département
// ─────────────────────────────────────────────
async function addDepartement() {
    const payload = {
        nom:         getVal('dept-nom'),
        code:        getVal('dept-code'),
        description: getVal('dept-desc'),
    };
    if (!payload.nom || !payload.code) {
        showToast('Nom et code sont obligatoires.', 'error');
        return;
    }
    await apiCall('POST', '/admin/api/departement', payload, () => {
        clearFields(['dept-nom','dept-code','dept-desc']);
    });
}

// ========== LISTE DES DÉPARTEMENTS ==========
async function loadDepartements() {
    const container = document.getElementById('departements-list');
    if (!container) return;
    container.innerHTML = '<p class="text-slate-500 text-sm">Chargement...</p>';
    try {
        const res = await fetch('/admin/api/departements', { credentials: 'include' });
        if (!res.ok) throw new Error();
        const data = await res.json();
        if (data.length === 0) {
            container.innerHTML = '<p class="text-slate-500 text-sm italic">Aucun département.</p>';
            return;
        }
        container.innerHTML = `
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Code</th>
                        <th>Nom</th>
                        <th>Description</th>
                        <th>Chef de département</th>
                    </tr>
                </thead>
                <tbody>
                    ${data.map(d => `
                        <tr>
                            <td>${d.code || '—'}</td>
                            <td>${d.nom || '—'}</td>
                            <td>${d.description || '—'}</td>
                            <td>${d.chef_nom ? `${d.chef_prenom || ''} ${d.chef_nom}` : '—'}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    } catch(e) {
        container.innerHTML = '<p class="text-red-400 text-sm">Erreur de chargement.</p>';
    }
}


// ─────────────────────────────────────────────
//  Ajouter une filière
// ─────────────────────────────────────────────
async function addFiliere() {
    const payload = {
        nom:      getVal('fil-nom'),
        code:     getVal('fil-code'),
        dept_nom: getVal('fil-dept'),
    };
    if (!payload.nom || !payload.code || !payload.dept_nom) {
        showToast('Tous les champs sont obligatoires.', 'error');
        return;
    }
    await apiCall('POST', '/admin/api/filiere', payload, () => {
        clearFields(['fil-nom','fil-code','fil-dept']);
    });
}


// ========== LISTE DES FILIÈRES ==========
async function loadFilieres() {
    const container = document.getElementById('filieres-list');
    if (!container) return;
    container.innerHTML = '<p class="text-slate-500 text-sm">Chargement...</p>';
    try {
        const res = await fetch('/admin/api/filieres', { credentials: 'include' });
        if (!res.ok) throw new Error();
        const data = await res.json();
        if (data.length === 0) {
            container.innerHTML = '<p class="text-slate-500 text-sm italic">Aucune filière créée.</p>';
            return;
        }
        container.innerHTML = `
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Code</th>
                        <th>Nom</th>
                        <th>Département parent</th>
                    </tr>
                </thead>
                <tbody>
                    ${data.map(f => `
                        <tr>
                            <td>${f.code || '—'}</td>
                            <td>${f.nom || '—'}</td>
                            <td>${f.departement || '—'}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    } catch(e) {
        container.innerHTML = '<p class="text-red-400 text-sm">Erreur de chargement.</p>';
    }
}


// ─────────────────────────────────────────────
//  Ajouter une UE
// ─────────────────────────────────────────────
function toggleSpecialiteField() {
    const type = getVal('ue-type');
    const field = document.getElementById('specialite-field');
    if (field) {
        field.classList.toggle('hidden', type !== 'specialite');
    }
}

async function addUE() {
    const payload = {
        code:          getVal('ue-code'),
        intitule:      getVal('ue-intitule'),
        credits:       parseInt(getVal('ue-credits')) || 3,
        semestre:      parseInt(getVal('ue-semestre')) || 1,
        type_cours:    getVal('ue-type'),
        niveau_rang:   parseInt(getVal('ue-niveau')) || 1,
        filiere_nom:   getVal('ue-filiere'),
        specialite_nom:getVal('ue-specialite') || '',
    };

    if (!payload.code || !payload.intitule || !payload.filiere_nom) {
        showToast('Code, intitulé et filière sont obligatoires.', 'error');
        return;
    }
    await apiCall('POST', '/admin/api/ue', payload, () => {
        clearFields(['ue-code','ue-intitule','ue-filiere','ue-specialite']);
    });
}

// ========== LISTE DES UNITÉS D'ENSEIGNEMENT ==========
async function loadUEs() {
    const container = document.getElementById('ues-list');
    if (!container) return;
    container.innerHTML = '<p class="text-slate-500 text-sm">Chargement...</p>';
    try {
        const res = await fetch('/admin/api/ues', { credentials: 'include' });
        if (!res.ok) throw new Error();
        const data = await res.json();
        if (data.length === 0) {
            container.innerHTML = '<p class="text-slate-500 text-sm italic">Aucune UE enregistrée.</p>';
            return;
        }
        container.innerHTML = `
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Code</th>
                        <th>Intitulé</th>
                        <th>Crédits</th>
                        <th>Semestre</th>
                        <th>Type</th>
                        <th>Filière</th>
                        <th>Niveau</th>
                        <th>Spécialité</th>
                        <th>Enseignants</th>
                    </tr>
                </thead>
                <tbody>
                    ${data.map(ue => `
                        <tr>
                            <td>${ue.code || '—'}</td>
                            <td>${ue.intitule || '—'}</td>
                            <td>${ue.credits || '—'}</td>
                            <td>${ue.semestre || '—'}</td>
                            <td>${ue.type_cours || '—'}</td>
                            <td>${ue.filiere}</td>
                            <td>${ue.niveau}</td>
                            <td>${ue.specialite}</td>
                            <td><span class="text-xs">${ue.enseignants}</span></td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    } catch(e) {
        container.innerHTML = '<p class="text-red-400 text-sm">Erreur de chargement.</p>';
    }
}

// ─────────────────────────────────────────────
//  Inscrire un étudiant
// ─────────────────────────────────────────────
async function addEtudiant() {
    const payload = {
        matricule:      getVal('etu-matricule'),
        nom:            getVal('etu-nom'),
        prenom:         getVal('etu-prenom'),
        sexe:           getVal('etu-sexe'),
        date_naissance: getVal('etu-naissance') || '',
        filiere_code:   getVal('etu-filiere'),
        niveau_rang:    parseInt(getVal('etu-niveau')) || 1,
    };

    if (!payload.matricule || !payload.nom || !payload.filiere_code) {
        showToast('Matricule, nom et filière sont obligatoires.', 'error');
        return;
    }
    await apiCall('POST', '/admin/api/etudiant', payload, () => {
        clearFields(['etu-matricule','etu-nom','etu-prenom','etu-naissance','etu-filiere']);
    });
}

// ========== LISTE DES ÉTUDIANTS ==========
async function loadEtudiants() {
    const container = document.getElementById('etudiants-list');
    if (!container) return;
    container.innerHTML = '<p class="text-slate-500 text-sm">Chargement...</p>';
    try {
        const res = await fetch('/admin/api/etudiants', { credentials: 'include' });
        if (!res.ok) throw new Error();
        const data = await res.json();
        if (data.length === 0) {
            container.innerHTML = '<p class="text-slate-500 text-sm italic">Aucun étudiant inscrit.</p>';
            return;
        }
        container.innerHTML = `
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Matricule</th>
                        <th>Nom</th>
                        <th>Prénom</th>
                        <th>Sexe</th>
                        <th>Date naissance</th>
                        <th>Filière</th>
                        <th>Niveau</th>
                    </tr>
                </thead>
                <tbody>
                    ${data.map(e => `
                        <tr>
                            <td>${e.matricule || '—'}</td>
                            <td>${e.nom || '—'}</td>
                            <td>${e.prenom || '—'}</td>
                            <td>${e.sexe || '—'}</td>
                            <td>${e.date_naissance || '—'}</td>
                            <td>${e.filiere || '—'}</td>
                            <td>${e.niveau_label || e.niveau_rang || '—'}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    } catch(e) {
        container.innerHTML = '<p class="text-red-400 text-sm">Erreur de chargement.</p>';
    }
}

// ─────────────────────────────────────────────
//  Liaisons
// ─────────────────────────────────────────────
async function linkEnseignantUE() {
    const payload = {
        enseignant_nom: getVal('lien-ens'),
        ue_code:        getVal('lien-ue'),
    };
    if (!payload.enseignant_nom || !payload.ue_code) {
        showToast('Nom enseignant et code UE sont obligatoires.', 'error');
        return;
    }
    await apiCall('POST', '/admin/api/enseigne', payload, () => {
        clearFields(['lien-ens','lien-ue']);
    });
}

async function setChefDept() {
    const payload = {
        enseignant_nom: getVal('chef-ens'),
        dept_nom:       getVal('chef-dept'),
    };
    if (!payload.enseignant_nom || !payload.dept_nom) {
        showToast('Nom enseignant et département sont obligatoires.', 'error');
        return;
    }
    await apiCall('POST', '/admin/api/chef', payload, () => {
        clearFields(['chef-ens','chef-dept']);
    });
}

// ─────────────────────────────────────────────
//  Maintenance BDD
// ─────────────────────────────────────────────
async function seedDatabase() {
    if (!confirm('Charger les données de démonstration ? Les données existantes seront conservées.')) return;
    await apiCall('POST', '/admin/api/seed', {}, () => {
        loadDashboardStats();
    });
}

async function clearDatabase() {
    if (!confirm('⚠️ ATTENTION : Cette action supprime INTÉGRALEMENT la base. Action irréversible. Continuer ?')) return;
    await apiCall('POST', '/admin/api/clear', {}, () => {
        loadDashboardStats();
    });
}

// ─────────────────────────────────────────────
//  Helper : appel API générique
// ─────────────────────────────────────────────
async function apiCall(method, url, body, onSuccess) {
    try {
        const res = await fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: method !== 'GET' ? JSON.stringify(body) : undefined,
        });

        const data = await res.json();

        if (res.ok) {
            showToast(data.message || 'Opération réussie.', 'success');
            if (onSuccess) onSuccess(data);
        } else if (res.status === 401 || res.status === 403) {
            showToast('Session expirée. Veuillez vous reconnecter.', 'error');
            setTimeout(() => window.location.href = '/admin/login', 1500);
        } else {
            showToast(data.error || data.message || 'Erreur serveur.', 'error');
        }
    } catch (err) {
        showToast('Erreur de connexion au serveur Flask.', 'error');
        console.error('apiCall error:', err);
    }
}

// ─────────────────────────────────────────────
//  Toast notifications
// ─────────────────────────────────────────────
let toastTimer = null;

function showToast(message, type = 'success') {
    const toast    = document.getElementById('toast');
    const iconEl   = document.getElementById('toast-icon');
    const titleEl  = document.getElementById('toast-title');
    const msgEl    = document.getElementById('toast-msg');

    if (!toast) return;

    const isSuccess = type === 'success';
    iconEl.innerHTML = isSuccess
        ? '<i class="fas fa-check-circle" style="color:#22c55e;font-size:18px;"></i>'
        : '<i class="fas fa-times-circle" style="color:#f87171;font-size:18px;"></i>';

    titleEl.textContent = isSuccess ? 'Succès' : 'Erreur';
    msgEl.textContent   = message;

    toast.style.borderColor = isSuccess ? 'rgba(34,197,94,0.3)' : 'rgba(239,68,68,0.3)';
    toast.classList.add('show');

    if (toastTimer) clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toast.classList.remove('show'), 4000);
}

// ─────────────────────────────────────────────
//  Helpers DOM
// ─────────────────────────────────────────────
function getVal(id) {
    const el = document.getElementById(id);
    return el ? el.value.trim() : '';
}

function clearFields(ids) {
    ids.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.value = '';
    });
}

function setText(id, val) {
    const el = document.getElementById(id);
    if (el) el.textContent = val;
}

// ========== SECRÉTAIRES ==========
async function addSecretaire() {
    const payload = {
        nom: getVal('sec-nom'),
        prenom: getVal('sec-prenom'),
        email: getVal('sec-email'),
        dept_nom: getVal('sec-dept')
    };
    if (!payload.nom || !payload.prenom || !payload.email || !payload.dept_nom) {
        showToast('Tous les champs sont obligatoires.', 'error');
        return;
    }
    await apiCall('POST', '/admin/api/secretaire', payload, () => {
        clearFields(['sec-nom','sec-prenom','sec-email','sec-dept']);
        loadSecretaires();
    });
}

async function loadSecretaires() {
    const container = document.getElementById('secretaires-list');
    if (!container) return;
    container.innerHTML = '<p class="text-slate-500 text-sm">Chargement...</p>';
    try {
        const res = await fetch('/admin/api/secretaires', { credentials: 'include' });
        if (!res.ok) throw new Error();
        const data = await res.json();
        if (data.length === 0) {
            container.innerHTML = '<p class="text-slate-500 text-sm italic">Aucune secrétaire enregistrée.</p>';
            return;
        }
       container.innerHTML = `
            <table class="data-table">
                <thead><tr><th>Nom</th><th>Prénom</th><th>Email</th><th>Département</th></tr></thead>
                <tbody>
                    ${data.map(s => `
                        <tr>
                            <td>${s.nom || ''}</td>
                            <td>${s.prenom || ''}</td>
                            <td><code>${s.email || ''}</code></td>
                            <td>${s.departement || '—'}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    } catch(e) {
        container.innerHTML = '<p class="text-red-400 text-sm">Erreur de chargement.</p>';
    }
}

// ========== DÉLÉGUÉS ==========
async function addDelegue() {
    const payload = {
        matricule: getVal('del-matricule'),
        groupe: getVal('del-groupe'),
        cible_nom: getVal('del-cible-nom'),
        cible_type: getVal('del-cible-type')
    };
    if (!payload.matricule || !payload.groupe || !payload.cible_nom) {
        showToast('Matricule, groupe et cible sont obligatoires.', 'error');
        return;
    }
    await apiCall('POST', '/admin/api/delegue', payload, () => {
        clearFields(['del-matricule','del-groupe','del-cible-nom']);
        loadDelegues();
    });
}

async function loadDelegues() {
    const container = document.getElementById('delegues-list');
    if (!container) return;
    container.innerHTML = '<p class="text-slate-500 text-sm">Chargement...</p>';
    try {
        const res = await fetch('/admin/api/delegues', { credentials: 'include' });
        if (!res.ok) throw new Error();
        const data = await res.json();
        if (data.length === 0) {
            container.innerHTML = '<p class="text-slate-500 text-sm italic">Aucun délégué désigné.</p>';
            return;
        }
        container.innerHTML = `
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Matricule</th>
                        <th>Nom</th>
                        <th>Prénom</th>
                        <th>Groupe</th>
                        <th>Filière</th>
                        <th>Niveau / Spécialité</th>
                    </tr>
                </thead>
                <tbody>
                    ${data.map(d => `
                        <tr>
                            <td>${d.matricule}</td>
                            <td>${d.nom}</td>
                            <td>${d.prenom}</td>
                            <td>${d.groupe}</td>
                            <td>${d.filiere}</td>
                            <td>${d.niveau_specialite}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    } catch(e) {
        container.innerHTML = '<p class="text-red-400 text-sm">Erreur de chargement.</p>';
    }
}


// ========== RELATIONS ENSEIGNANT-UE ==========
async function loadEnseigneRelations() {
    const container = document.getElementById('enseigne-list');
    if (!container) return;
    container.innerHTML = '<p class="text-slate-500 text-sm">Chargement...</p>';
    try {
        const res = await fetch('/admin/api/enseigne_relations', { credentials: 'include' });
        if (!res.ok) throw new Error();
        const data = await res.json();
        if (data.length === 0) {
            container.innerHTML = '<p class="text-slate-500 text-sm italic">Aucune liaison enseignant-UE trouvée.</p>';
            return;
        }
        container.innerHTML = `
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Enseignant</th>
                        <th>UE Code</th>
                        <th>UE Intitulé</th>
                    </tr>
                </thead>
                <tbody>
                    ${data.map(row => `
                        <tr>
                            <td>${row.enseignant_titre || ''} ${row.enseignant_prenom || ''} ${row.enseignant_nom || ''}</td>
                            <td>${row.ue_code || '—'}</td>
                            <td>${row.ue_intitule || '—'}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    } catch(e) {
        container.innerHTML = '<p class="text-red-400 text-sm">Erreur de chargement.</p>';
    }
}

async function loadChefsDepartement() {
    const container = document.getElementById('chefs-list');
    if (!container) return;
    container.innerHTML = '<p class="text-slate-500 text-sm">Chargement...</p>';
    try {
        const res = await fetch('/admin/api/chefs_departement', { credentials: 'include' });
        if (!res.ok) throw new Error();
        const data = await res.json();
        if (data.length === 0) {
            container.innerHTML = '<p class="text-slate-500 text-sm italic">Aucun chef de département désigné.</p>';
            return;
        }
        container.innerHTML = `
            <table class="data-table">
                <thead>
                    <tr><th>Département</th><th>Chef</th></tr>
                </thead>
                <tbody>
                    ${data.map(row => `
                        <tr>
                            <td>${row.departement || '—'}</td>
                            <td>${row.enseignant_titre || ''} ${row.enseignant_prenom || ''} ${row.enseignant_nom || ''}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    } catch(e) {
        container.innerHTML = '<p class="text-red-400 text-sm">Erreur de chargement.</p>';
    }
}

async function loadSpecialites() {
    const container = document.getElementById('specialites-list');
    if (!container) return;
    container.innerHTML = '<p class="text-slate-500 text-sm">Chargement...</p>';
    try {
        const res = await fetch('/admin/api/specialites', { credentials: 'include' });
        if (!res.ok) throw new Error();
        const data = await res.json();
        if (data.length === 0) {
            container.innerHTML = '<p class="text-slate-500 text-sm italic">Aucune spécialité trouvée.</p>';
            return;
        }
        container.innerHTML = `
    <table class="data-table">
        <thead>
            <tr><th>Code</th><th>Nom</th><th>Filière</th></tr>
        </thead>
        <tbody>
            ${data.map(sp => `
                <tr>
                    <td>${sp.code}</td>
                    <td>${sp.nom}</td>
                    <td>${sp.filiere}</td>
                </tr>
            `).join('')}
        </tbody>
    </table>
`;
    } catch(e) {
        container.innerHTML = '<p class="text-red-400 text-sm">Erreur de chargement.</p>';
    }
}