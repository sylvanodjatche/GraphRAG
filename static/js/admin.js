/**
 * UNIGRAPH - Logique d'administration (Master 1)
 * Gère les interactions avec l'API Neo4j via Flask
 */

// --- 1. GESTION DES ENSEIGNANTS ---
async function addEnseignant() {
    const payload = {
        nom: document.getElementById('ens-nom').value.trim(),
        titre: document.getElementById('ens-titre').value,
        grade: document.getElementById('ens-grade').value.trim(),
        email: document.getElementById('ens-email').value.trim()
    };

    if (!payload.nom || !payload.grade) {
        showToast("Veuillez remplir au moins le nom et le grade.", true);
        return;
    }

    try {
        const res = await fetch('/api/add_enseignant', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        
        if (res.ok) {
            showToast(data.message);
            document.getElementById('ens-nom').value = "";
            document.getElementById('ens-grade').value = "";
            document.getElementById('ens-email').value = "";
        } else {
            showToast("Erreur serveur : " + data.message, true);
        }
    } catch (e) {
        showToast("Erreur de connexion au serveur.", true);
    }
}

// --- 2. GESTION DES COURS & LIAISONS ---
async function addCours() {
    const payload = {
        nom: document.getElementById('crs-nom').value.trim(),
        code: document.getElementById('crs-code').value.trim(),
        niveau: document.getElementById('crs-niveau').value.trim(),
        semestre: document.getElementById('crs-semestre').value,
        filiere: document.getElementById('crs-filiere').value.trim(),
        enseignant: document.getElementById('crs-enseignant').value.trim(),
        salle: document.getElementById('crs-salle').value.trim()
    };

    if (!payload.nom || !payload.code || !payload.filiere) {
        showToast("Le nom, le code et la filière sont obligatoires.", true);
        return;
    }

    try {
        const res = await fetch('/api/add_cours', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();

        if (res.ok) {
            showToast(data.message);
            document.getElementById('crs-nom').value = "";
            document.getElementById('crs-code').value = "";
        } else {
            showToast("Erreur : " + data.message, true);
        }
    } catch (e) {
        showToast("Erreur de communication avec l'API.", true);
    }
}

// --- 3. FONCTIONS UTILITAIRES (SORTIES DE ADDCOURS) ---

function showToast(msg, isError = false) {
    const toast = document.getElementById('toast');
    const toastMsg = document.getElementById('toast-msg');
    const toastIcon = document.getElementById('toast-icon');

    toastMsg.innerText = msg;
    toastIcon.innerHTML = isError ? 
        '<i class="fas fa-times-circle text-red-400"></i>' : 
        '<i class="fas fa-check-circle text-green-400"></i>';
    
    toast.classList.remove('translate-y-20', 'opacity-0');
    setTimeout(() => {
        toast.classList.add('translate-y-20', 'opacity-0');
    }, 3000);
}

async function clearDB() {
    if(!confirm("⚠️ ATTENTION : Cette action va supprimer l'intégralité du graphe Neo4j. Continuer ?")) return;
    
    try {
        const res = await fetch('/api/clear', { method: 'POST' });
        const data = await res.json();
        showToast(data.message);
    } catch (e) {
        showToast("Erreur lors de la réinitialisation", true);
    }
}