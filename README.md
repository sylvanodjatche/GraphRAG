
# UNIGRAPH – Graphe de connaissances et assistant académique

## Description
UNIGRAPH est une application web combinant une base de données graphe (Neo4j) et un modèle de langage (Groq/Llama 3) pour répondre aux questions des étudiants de la Faculté des Sciences de l’Université de Yaoundé I. Elle permet l’administration complète des données (enseignants, UE, étudiants, spécialités) et la visualisation interactive du graphe.

## Outils requis
- **Python 3.10+** (backend)
- **Neo4j** (base de données graphe) – version Community ou Enterprise
- **Docker** (optionnel, pour le cluster distribué)
- **Git** (pour cloner le dépôt)
- **Navigateur récent** (Firefox, Chrome, Edge)
- **Compte Groq** (pour obtenir une clé API gratuite)

## Installation et configuration

### 1. Cloner le dépôt

git clone https://github.com/sylvanodjatche/GraphRAG.git
cd GraphRAG

2. Créer un environnement virtuel Python

python3 -m venv venv
source venv/bin/activate        # Sur Linux/Mac
# venv\Scripts\activate         # Sur Windows

3. Installer les dépendances Python

pip install --upgrade pip
pip install -r requirements.txt

4. Installer Neo4j (mode local)

Téléchargez Neo4j Community : https://neo4j.com/download/

Installez-le et démarrez-le (port par défaut : 7687).

Créez une base avec les identifiants neo4j / password123 (ou modifiez le fichier .env).

Alternative rapide avec Docker (si Docker est installé) :

docker run --name neo4j -p 7687:7687 -p 7474:7474 -e NEO4J_AUTH=neo4j/password123 -d neo4j:latest

5. Configurer les variables d’environnement

Créez un fichier .env à la racine du projet. Demandez aux administrateurs le fichier complet, ou utilisez le modèle ci-dessous en remplaçant les valeurs par les vôtres :


# Clé API Groq (obtenue sur https://console.groq.com)
GROQ_API_KEY=votre_clé_ici

# Connexion Neo4j locale
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password123

# Super administrateur (vous)
ADMIN_EMAIL=votre@email.com
ADMIN_PASSWORD=votre_mot_de_passe

# Administrateurs secondaires (séparés par des virgules)
ADMIN_EMAILS=collegue1@exemple.com,collegue2@exemple.com
ADMIN_COMMON_PASSWORD=unigraph237

# Google OAuth (optionnel – pour la connexion avec Google)
GOOGLE_CLIENT_ID=votre_client_id
GOOGLE_CLIENT_SECRET=votre_client_secret
GOOGLE_REDIRECT_URI=http://127.0.0.1:5000/auth/google/callback

# Sécurité Flask
FLASK_SECRET_KEY=une_cle_secrete_longue_et_aleatoire
JWT_SECRET_KEY=une_autre_cle_longue
FLASK_ENV=development

Note : Pour obtenir GOOGLE_CLIENT_ID et GOOGLE_CLIENT_SECRET, créez un projet sur Google Cloud Console, activez l’API OAuth 2.0 et configurez l’URI de redirection http://127.0.0.1:5000/auth/google/callback.

6. Initialiser la base de données (première installation)


python ingest_data.py                # Crée la structure (département, filières, UE, enseignants)
python add_m1_students.py            # Ajoute les 100 étudiants de M1
python add_specialite_relation.py    # Lie chaque étudiant à sa spécialité

7. Lancer l’application

python app.py
Ouvrez votre navigateur à l’adresse : http://127.0.0.1:5000

Utilisation
Chatbot
Posez des questions en français. Exemples :

« Qui dirige le département Informatique ? »

« Quels sont les étudiants de la spécialité SD en M1 ? »

« Quelles unités d’enseignement sont dispensées en M1 ? »

« Donne-moi la photo du Dr Tapamo »

Administration
Le lien « Administration » n’apparaît que lorsque vous êtes connecté en tant qu’administrateur.

Connectez-vous via /admin/login avec votre email et mot de passe (ou Google OAuth).

Une fois connecté, vous pouvez ajouter, modifier ou supprimer des données (enseignants, UE, étudiants, secrétaires, délégués, etc.), visualiser les statistiques et l’état du cluster Neo4j.

Visualisation du graphe
Dans le chat, cliquez sur « Visualiser le graphe ».

Cliquez sur un nœud pour ne garder que ses voisins directs (filtrage interactif).

Utilisez le bouton « Réinitialiser » pour revenir à l’affichage complet.

Démarrer le cluster Neo4j distribué (démonstration)
bash
docker-compose up -d
Cette commande lance trois conteneurs Neo4j :

nœud 1 (leader) sur le port 7687

nœud 2 (replica) sur le port 7688

nœud 3 (replica) sur le port 7689

Vous pouvez ainsi démontrer la haute disponibilité et la réplication.

Dépannage courant
Problème	Solution
ModuleNotFoundError	Activez l’environnement virtuel (source venv/bin/activate).
Impossible de se connecter à Neo4j	Vérifiez que Neo4j est démarré (docker ps ou service Neo4j). Vérifiez les identifiants dans .env.
RateLimitError de Groq	Le quota gratuit (100 000 tokens/jour) est atteint. Attendez la réinitialisation (environ une journée) ou changez de clé API.
Le chat ne répond pas	Ouvrez la console du navigateur (F12) et vérifiez les erreurs JavaScript.
Les images des enseignants ne s’affichent pas	Vérifiez que l’URL dans la base Neo4j est correcte (exécutez MATCH (e:Enseignant) RETURN e.nom, e.photo_url dans Neo4j Browser).
Contribution
Les membres de l’équipe peuvent travailler sur des branches séparées et soumettre des pull requests vers main.
Contactez l’administrateur principal pour obtenir les droits d’écriture sur le dépôt.

Auteur
Sylvano Djatche – Projet UNIGRAPH, Faculté des Sciences, Université de Yaoundé I.

Licence
Ce projet est distribué à des fins éducatives uniquement.

