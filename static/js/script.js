const chatWindow = document.getElementById('chat-window');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');

// Fonction pour l'effet "machine à écrire" (Dynamisme Master 1)
function typeEffect(element, text, speed = 20) {
    let i = 0;
    element.innerHTML = ""; // On vide le "..." avant de commencer
    function type() {
        if (i < text.length) {
            element.innerHTML += text.charAt(i);
            i++;
            setTimeout(type, speed);
            // On force le scroll vers le bas à chaque nouveau caractère
            chatWindow.scrollTop = chatWindow.scrollHeight;
        }
    }
    type();
}

async function askQuestion() {
    const question = userInput.value.trim();
    if (!question) return;

    // 1. Ajouter la bulle utilisateur avec la classe d'animation
    chatWindow.innerHTML += `
        <div class="message-bubble gap-3 max-w-3xl ml-auto flex-row-reverse">
            <div class="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center text-white text-xs shrink-0">
                <i class="fas fa-user"></i>
            </div>
            <div class="bg-blue-600 text-white p-4 rounded-2xl rounded-tr-none shadow-sm">
                ${question}
            </div>
        </div>
    `;

    // Nettoyage de l'input et focus
    userInput.value = "";
    chatWindow.scrollTop = chatWindow.scrollHeight;

    // 2. Appel à l'API Flask
    try {
        const response = await fetch('/ask', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question: question })
        });
        
        const data = await response.json();

        // 3. Créer la bulle de réponse de l'IA (initialement vide avec "...")
        const responseId = 'resp-' + Date.now();
        chatWindow.innerHTML += `
            <div class="message-bubble gap-3 max-w-3xl">
                <div class="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white text-xs shrink-0">
                    <i class="fas fa-robot"></i>
                </div>
                <div id="${responseId}" class="bg-white p-4 rounded-2xl rounded-tl-none shadow-sm border border-slate-100 text-slate-800">
                    En cours de réflexion...
                </div>
            </div>
        `;

        // 4. Lancer l'effet d'écriture sur la réponse reçue
        const responseDiv = document.getElementById(responseId);
        if (data.answer) {
            typeEffect(responseDiv, data.answer);
        } else if (data.error) {
            responseDiv.innerHTML = `<span class="text-red-500 italic">Erreur : ${data.error}</span>`;
        }

    } catch (error) {
        console.error("Erreur de connexion:", error);
        chatWindow.innerHTML += `<p class="text-center text-red-400 text-xs italic">Erreur de connexion au serveur</p>`;
    }
}

// Écouteurs d'événements
sendBtn.addEventListener('click', askQuestion);

userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        askQuestion();
    }
});

let network = null;

async function toggleGraph() {
    const container = document.getElementById('graph-container');
    
    if (container.classList.contains('hidden')) {
        container.classList.remove('hidden');
        await loadGraph();
    } else {
        container.classList.add('hidden');
    }
}

async function loadGraph() {
    const response = await fetch('/graph-data');
    const data = await response.json();

    const container = document.getElementById('mynetwork');
    const options = {
        nodes: {
            shape: 'dot',
            size: 16,
            font: { size: 12, face: 'Tahoma' }
        },
        edges: {
            arrows: { to: { enabled: true } },
            font: { align: 'middle' },
            color: '#94a3b8'
        },
        groups: {
            Enseignant: { color: { background: '#60a5fa', border: '#2563eb' } },
            Cours: { color: { background: '#f87171', border: '#dc2626' } },
            Etudiant: { color: { background: '#fbbf24', border: '#d97706' } },
            Departement: { color: { background: '#34d399', border: '#059669' } }
        },
        physics: { stabilization: true }
    };

    if (network !== null) {
        network.destroy();
    }
    network = new vis.Network(container, data, options);
}