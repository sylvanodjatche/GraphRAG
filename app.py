import os
from flask import Flask, render_template, request, jsonify  # Ajoute render_template
from groq import Groq
from neo4j import GraphDatabase
from dotenv import load_dotenv
from database import UnigraphDB
db_manager = UnigraphDB()
load_dotenv()


app = Flask(__name__)

# Connexion aux services
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"), 
    auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))
)

def query_graph(cypher_query):
    """Exécute une requête directement dans Neo4j"""
    with driver.session() as session:
        result = session.run(cypher_query)
        return [record.data() for record in result]


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    user_question = request.json.get("question")
    
    # 1. Groq transforme la question en Cypher (Prompt renforcé)
    
    system_prompt = """
    Tu es un expert Neo4j pour le projet UNIGRAPH. Ta mission est de générer une requête Cypher parfaite.

    DIRECTIVES DE ROBUSTESSE (SÉCURITÉ MASTER 1) :
    1. TOLÉRANCE AUX ERREURS : Ignore la casse (majuscules/minuscules), les accents et le pluriel de l'utilisateur.
    2. NORMALISATION DES DONNÉES : 
    - Les noms de cours, départements et codes sont stockés en MAJUSCULES dans la base (ex: "INFORMATIQUE", "INF4038").
    - Convertis systématiquement les termes de recherche de l'utilisateur en MAJUSCULES dans ta requête.
    3. RECHERCHE FLEXIBLE : Utilise 'CONTAINS' ou des expressions régulières pour éviter les échecs sur un mot partiel.
    4. LABELS DISPONIBLES : Departement, Filiere, Cours, Enseignant, Etudiant, Salle.
    5. Instruction à ajouter : "Les enseignants ont des propriétés distinctes : nom, prenom, titre, grade et email . Pour chercher un enseignant par son nom, utilise toujours toUpper(e.nom) CONTAINS '...'."
    RELATIONS :
    - (Enseignant)-[:ENSEIGNE]->(Cours)
    - (Cours)-[:PROPOSE_DANS]->(Filiere)
    - (Filiere)-[:APPARTIENT_A]->(Departement)
    - (Etudiant)-[:INSCRIT_A]->(Cours)
    - (Cours)-[:SE_DEROULE_DANS]->(Salle)

    EXEMPLE DE GÉNÉRATION :
    Question : "qui enseigne l'informatique ?"
    Requête : MATCH (e:Enseignant)-[:ENSEIGNE]->(c:Cours) WHERE c.nom CONTAINS 'INFORMATIQUE' RETURN e.nom

    STRUCTURE DES ENSEIGNANTS :
    - Les enseignants ont les propriétés : nom, prenom, titre, grade, email.
    - Le 'nom' est stocké en MAJUSCULES (ex: 'TAPAMO').
    - Le 'titre' est le titre académique (ex: 'Pr', 'Dr', 'Mr').
    
    CONSIGNE DE RÉPONSE :
    - Ne réponds pas juste 'TAPAMO'. 
    - Formule toujours avec le titre et le nom pour être respectueux.
    - Exemple de réponse : 'Le cours est enseigné par le {titre} {nom}, qui est {grade}.'
    
    EXEMPLE DE REQUÊTE :
    Question : 'Qui est Tapamo ?'
    Requête : MATCH (e:Enseignant) WHERE toUpper(e.nom) CONTAINS 'TAPAMO' RETURN e.titre, e.nom, e.grade, e.email

    RÈGLES CRITIQUES :
    0.Lors d'une recherche d'enseignant, ne filtre jamais par le titre dans la clause WHERE (ex: évite e.titre = 'Dr'). Cherche uniquement par le nom. Utilise les titres et grades uniquement pour construire la phrase de réponse finale, EXEMPLE :
    Question : "Qui est le Pr Tapamo ?"
    Requête : MATCH (e:Enseignant) WHERE toUpper(e.nom) CONTAINS 'TAPAMO' RETURN e.titre, e.nom, e.grade, e.email
    1. SYNTAXE DE MATCH UNIQUE : Ne déclare jamais de variables dans le WHERE. Déclare tout le chemin dans le MATCH.
       MAUVAIS : MATCH (e) WHERE (e)-[:REL]->(s)
       BON : MATCH (e)-[:REL]->(s)
    2. PAS DE 'UNION' : Utilise un seul chemin continu.
    3. SCHÉMA DE RÉFÉRENCE :
       - Pour l'Amphi : (e:Etudiant)-[:INSCRIT_A]->(c:Cours)-[:SE_DEROULE_DANS]->(s:Salle)
       - Pour le Département : (e:Etudiant)-[:INSCRIT_A]->(c:Cours)-[:PROPOSE_DANS]->(f:Filiere)-[:APPARTIENT_A]->(d:Departement)
    4. SÉCURITÉ : Si l'utilisateur demande une relation inexistante (ex: femme, enfant), réponds que tu n'as pas l'information.
    RÈGLE D'OR : Réponds UNIQUEMENT avec la requête Cypher. Pas de texte, pas de balises ```.
    """
    
    chat_completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_question}
        ],
        model="llama-3.3-70b-versatile",
    )
    
    # Nettoyage automatique des balises au cas où l'IA en ajoute quand même
    cypher_query = chat_completion.choices[0].message.content.strip()
    cypher_query = cypher_query.replace("```cypher", "").replace("```", "").strip()

    # 2. Exécution dans Neo4j
    try:
        data = query_graph(cypher_query)
        
        # 3. Réponse finale
        final_response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Tu es l'assistant d'Unigraph. Réponds en français de manière concise."},
                {"role": "user", "content": f"Question: {user_question} | Données trouvées: {data}"}
            ],
            model="llama-3.3-70b-versatile",
        )
        return jsonify({
            "answer": final_response.choices[0].message.content,
            "debug_query": cypher_query,
            "query": cypher_query  # On ajoute la requête brute ici
        })
    except Exception as e:
        return jsonify({"error": str(e), "attempted_query": cypher_query})
    

@app.route('/graph-data')
def get_graph_data():
    # On demande explicitement les IDs et les labels à Neo4j
    query = """
    MATCH (n)
    OPTIONAL MATCH (n)-[r]->(m)
    RETURN 
        id(n) as source_id, labels(n)[0] as source_label, n as source_data,
        type(r) as rel_type,
        id(m) as target_id, labels(m)[0] as target_label, m as target_data
    """
    
    with driver.session() as session:
        results = session.run(query)
        
        nodes = []
        edges = []
        node_ids = set()

        for record in results:
            # Traitement du nœud source (n)
            s_id = record["source_id"]
            if s_id is not None and s_id not in node_ids:
                data = record["source_data"]
                name = data.get('nom') or data.get('matricule') or "Nœud"
                nodes.append({
                    "id": s_id,
                    "label": f"{record['source_label']}\n({name})",
                    "group": record['source_label']
                })
                node_ids.add(s_id)

            # Traitement du nœud cible (m)
            t_id = record["target_id"]
            if t_id is not None and t_id not in node_ids:
                data = record["target_data"]
                name = data.get('nom') or data.get('matricule') or "Nœud"
                nodes.append({
                    "id": t_id,
                    "label": f"{record['target_label']}\n({name})",
                    "group": record['target_label']
                })
                node_ids.add(t_id)

            # Traitement de la relation (r)
            if record["rel_type"]:
                edges.append({
                    "from": s_id,
                    "to": t_id,
                    "label": record["rel_type"]
                })

        return jsonify({"nodes": nodes, "edges": edges})
    
# Route pour afficher la page d'administration
@app.route('/admin')
def admin_page():
    return render_template('admin.html')

# Endpoint pour vider la base
@app.route('/api/clear', methods=['POST'])
def api_clear():
    db_manager.clear_database()
    return jsonify({"message": "Base de données vidée avec succès !"})

# Endpoint pour ajouter un enseignant via l'interface
@app.route('/api/add_enseignant', methods=['POST'])
def api_add_enseignant():
    data = request.json
    db_manager.add_enseignant(data['nom'], data['titre'], data['grade'], data['email'])
    return jsonify({"message": f"Enseignant {data['nom']} ajouté !"})

# Endpoint pour ajouter un cours (incluant les liaisons)
@app.route('/api/add_cours', methods=['POST'])
def api_add_cours():
    data = request.json
    db_manager.add_cours(
        data['nom'], data['code'], data['niveau'], data['semestre'],
        data['filiere'], data['enseignant'], data['salle']
    )
    return jsonify({"message": f"Cours {data['code']} créé et lié !"})    
if __name__ == '__main__':
    print("🚀 Serveur Unigraph démarré sur http://127.0.0.1:5000")
    app.run(port=5000, debug=True)