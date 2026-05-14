"""
UNIGRAPH — Backend principal
Flask + Neo4j + Groq + JWT + Google OAuth
"""

import os
import json
import datetime
from functools import wraps

from flask import (Flask, render_template, request, jsonify,
                   redirect, url_for, session, make_response)
from flask_cors import CORS
from flask_jwt_extended import (JWTManager, create_access_token,
                                jwt_required, get_jwt_identity,
                                set_access_cookies, unset_jwt_cookies,
                                verify_jwt_in_request)
from flask_bcrypt import Bcrypt
from groq import Groq
from neo4j import GraphDatabase
from dotenv import load_dotenv
from authlib.integrations.requests_client import OAuth2Session

from database import UnigraphDB

load_dotenv()

# ─────────────────────────────────────────────
#  Initialisation de l'application
# ─────────────────────────────────────────────
app = Flask(__name__)
CORS(app)

app.config["JWT_ACCESS_COOKIE_NAME"] = "access_token_cookie" # Nom par défaut de Flask-JWT
app.config["SECRET_KEY"]               = os.getenv("FLASK_SECRET_KEY", "dev-secret")
app.config["JWT_SECRET_KEY"]           = os.getenv("JWT_SECRET_KEY", "jwt-secret")
app.config["JWT_TOKEN_LOCATION"]       = ["cookies", "headers"]
app.config["JWT_COOKIE_SECURE"]        = False   # True en production HTTPS
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = datetime.timedelta(hours=8)
app.config["JWT_COOKIE_CSRF_PROTECT"]  = False   # Simplifié pour dev

# --- Dans la configuration de l'app ---
app.config['JWT_ACCESS_COOKIE_PATH'] = '/'                # Important pour que /admin y accède

jwt_manager = JWTManager(app)
bcrypt      = Bcrypt(app)
db_manager  = UnigraphDB()

# ─────────────────────────────────────────────
#  Clients externes
# ─────────────────────────────────────────────
groq_client  = Groq(api_key=os.getenv("GROQ_API_KEY"))
neo4j_driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"),
    auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))
)

# Identifiants admin depuis .env
SUPER_ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@unigraph.cm")
SUPER_ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Admin2026!")

ADMIN_EMAILS_STR = os.getenv("ADMIN_EMAILS", "")
ADMIN_EMAILS = [email.strip().lower() for email in ADMIN_EMAILS_STR.split(",") if email.strip()]
ADMIN_COMMON_PASSWORD = os.getenv("ADMIN_COMMON_PASSWORD", "unigraph237")

# Fusion pour la vérification de rôle (Google OAuth, etc.)
ALL_ADMIN_EMAILS = [SUPER_ADMIN_EMAIL.lower()] + ADMIN_EMAILS

# Google OAuth config
GOOGLE_CLIENT_ID     = os.getenv("GOOGLE_CLIENT_ID",    "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI  = os.getenv("GOOGLE_REDIRECT_URI",
                                  "http://127.0.0.1:5000/auth/google/callback")


# ─────────────────────────────────────────────
#  Helper Neo4j
# ─────────────────────────────────────────────
def query_graph(cypher_query, params=None):
    with neo4j_driver.session() as s:
        result = s.run(cypher_query, params or {})
        return [record.data() for record in result]


# ─────────────────────────────────────────────
#  Décorateur : admin requis
# ─────────────────────────────────────────────
def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
            identity = get_jwt_identity().lower()
            if identity in ALL_ADMIN_EMAILS:
                return fn(*args, **kwargs)
            return jsonify({"error": "Accès réservé"}), 403
        except Exception as e:
            print(f"Erreur Auth Admin: {e}")
            if "text/html" in request.headers.get("Accept", ""):
                return redirect(url_for("admin_login_page"))
            return jsonify({"error": "Non authentifié"}), 401
    return wrapper
# ═════════════════════════════════════════════
#  ROUTES PUBLIQUES
# ═════════════════════════════════════════════

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/ask", methods=["POST"])
def ask():
    user_question = request.json.get("question", "").strip()
    if not user_question:
        return jsonify({"error": "Question vide"}), 400

    system_prompt = """
Tu es un expert Neo4j pour le projet UNIGRAPH de la Faculte des Sciences de l'Universite de Yaounde I.
Ta mission : generer une requete Cypher parfaite basee sur le schema ci-dessous.

SCHEMA DU GRAPHE :
Noeuds : Departement, Filiere, Niveau, TypeCours, Specialite, UE, Enseignant, Etudiant, Secretaire
Relations :
  (Departement)-[:CONTIENT]->(Filiere)
  (Departement)<-[:DIRIGE]-(Enseignant)
  (Departement)<-[:RATTACHEE_A]-(Secretaire)
  (Filiere)-[:A_NIVEAU]->(Niveau)
  (Niveau)-[:INCLUT_TYPE]->(TypeCours)
  (TypeCours)-[:CONTIENT_UE]->(UE)
  (TypeCours {type:"specialite"})-[:REGROUPE]->(Specialite)
  (Specialite)-[:CONTIENT_UE]->(UE)
  (Enseignant)-[:ENSEIGNE]->(UE)
  (Etudiant)-[:INSCRIT_DANS]->(Filiere)
  (Etudiant)-[:EST_EN]->(Niveau)
  (Etudiant)-[:EST_DELEGUE {groupe}]->(Niveau)
  (Etudiant)-[:EST_DELEGUE {groupe}]->(Specialite)
  (Etudiant)-[:EST_SPECIALISE_DANS]->(Specialite)

PROPRIETES DES NOEUDS :
  Departement  : nom (MAJUSCULES), code, description
  Filiere      : nom (MAJUSCULES), code
  Niveau       : rang (1-5), label (L1/L2/L3/M1/M2), filiere (code filiere, ex: 'INFO' pour INFORMATIQUE)
  TypeCours    : type (fondamental|optionnel|specialite), filiere, niveau_rang
  Specialite   : nom (MAJUSCULES), code, filiere, niveau_rang
  UE           : code, intitule (MAJUSCULES), credits, semestre, type
  Enseignant   : nom (MAJUSCULES), prenom, titre (Mr/Dr/Pr), grade, email, photo_url
  Etudiant     : matricule, nom (MAJUSCULES), prenom, sexe, date_naissance, specialite
  Secretaire   : nom, prenom, email

REGLES CRITIQUES :
1. Cherche toujours avec toUpper() pour ignorer la casse.
2. Utilise CONTAINS pour les recherches partielles.
3. Ne filtre JAMAIS par titre (Dr/Pr) dans WHERE.
4. Retourne toujours nom, prenom, titre, grade pour les enseignants.
5. Reponds UNIQUEMENT avec la requete Cypher brute. Aucun texte, aucune balise ```.
6. Utilise toujours des alias explicites (AS) pour les colonnes retournees, sans prefixe de variable.
7. Pour interroger les specialites, utilise de preference leur code (propriete 'code') plutot que leur nom complet, Pour interroger les specialites, utilise de preference leur code (propriete 'code') plutot que leur nom complet(Quand l’utilisateur dit ‘data science’ou ‘science de donnees’, utilise le code ‘SD’;'securite informatique' ou securite',  utilise le code ‘SE’;'reseaux et systeme’ ou 'reseaux informatique', utilise le code ‘RS’;'Genie logiciel’, utilise le code ‘GL’.).

8. Pour les nœuds Niveau, la propriete 'filiere' contient le code de la filiere (ex: 'INFO'), pas son nom complet.
9. N'utilise JAMAIS de motif dans la clause WHERE. Place tous les motifs (relations, variables) dans le MATCH principal. La clause WHERE sert uniquement a filtrer sur des proprietes (ex: toUpper(u.intitule) CONTAINS ...).

EXEMPLES :
Question : "Qui dirige le departement informatique ?"
Requete : MATCH (d:Departement)<-[:DIRIGE]-(e:Enseignant) WHERE toUpper(d.nom) CONTAINS 'INFORMATIQUE' RETURN e.titre AS titre, e.nom AS nom, e.prenom AS prenom, e.grade AS grade, e.email AS email

Question : "Quels cours sont en L2 ?"
Requete : MATCH (n:Niveau {rang:2, filiere:'INFO'})-[:INCLUT_TYPE]->(tc:TypeCours)-[:CONTIENT_UE]->(u:UE) RETURN u.code AS code, u.intitule AS intitule, u.credits AS credits, tc.type AS type ORDER BY code

Question : "Qui enseigne Machine Learning ?"
Requete : MATCH (e:Enseignant)-[:ENSEIGNE]->(u:UE) WHERE toUpper(u.intitule) CONTAINS 'MACHINE LEARNING' RETURN e.titre AS titre, e.nom AS nom, e.prenom AS prenom, e.grade AS grade

Question : "Quelles specialites en M1 ?"
Requete : MATCH (n:Niveau {rang:4, filiere:'INFO'})-[:INCLUT_TYPE]->(tc:TypeCours {type:'specialite'})-[:REGROUPE]->(sp:Specialite) RETURN sp.code AS code, sp.nom AS nom

Question : "Quels sont les etudiants de la specialite SD en M1 ?"
Requete : MATCH (n:Niveau {rang:4, filiere:'INFO'})<-[:EST_EN]-(e:Etudiant)-[:EST_SPECIALISE_DANS]->(sp:Specialite {code:'SD'}) RETURN e.nom, e.prenom

Question : "Quel enseignant donne le cours de BASE DE DONNEES DISTRIBUEES en M1 ?"
Requete : MATCH (e:Enseignant)-[:ENSEIGNE]->(u:UE)<-[:CONTIENT_UE]-(tc:TypeCours)-[:INCLUT_TYPE]->(n:Niveau {rang:4, filiere:'INFO'}) WHERE toUpper(u.intitule) CONTAINS 'BASE DE DONNEES DISTRIBUEES' RETURN e.titre AS titre, e.nom AS nom, e.prenom AS prenom, e.grade AS grade
"""

    # Étape 1 : Groq génère la requête Cypher
    cypher_resp = groq_client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_question}
        ],
        model="llama-3.3-70b-versatile",# model="llama-3.1-8b-instant",model ="mixtral-8x7b-32768"
        temperature=0.1
    )
    cypher_query = cypher_resp.choices[0].message.content.strip()
    cypher_query = cypher_query.replace("```cypher", "").replace("```", "").strip()

    # Étape 2 : Exécution dans Neo4j
    try:
        data = query_graph(cypher_query)

        # Étape 3 : Groq formule la réponse naturelle
        final_resp = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": (
                    "Tu es l'assistant UNIGRAPH de la Faculte des Sciences de l'Universite de Yaounde I. "
                    "Reponds en francais, de facon claire et respectueuse. "
                    "Les donnees fournies sont sous forme de liste d'objets JSON. Chaque objet contient des champs comme 'nom', 'prenom', 'titre', etc. "
                    "IMPORTANT : Si la requete Cypher utilisee contient la relation [:DIRIGE], alors l'enseignant retourne est le chef de departement. "
                    "Tu dois donc repondre : 'Le departement X est dirige par [titre] [prenom] [nom], [grade].' "
                    "Si la liste est vide, dis poliment que l'information n'est pas disponible. "
                    "N'invente jamais de noms ou de donnees."
                )},
                {"role": "user", "content": (
                    f"Question posee : {user_question}\n"
                    f"Requete Cypher utilisee : {cypher_query}\n"
                    f"Donnees recuperees depuis la base : {json.dumps(data, ensure_ascii=False)}\n"
                    "Formule une reponse claire et naturelle en francais."
                )}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.3
        )

        return jsonify({
            "answer":      final_resp.choices[0].message.content,
            "debug_query": cypher_query,
            "raw_data":    data
        })

    except Exception as e:
        return jsonify({
            "error":           str(e),
            "attempted_query": cypher_query
        }), 500

# ─────────────────────────────────────────────
#  Données du graphe pour visualisation
# ─────────────────────────────────────────────
@app.route("/graph-data")
def get_graph_data():
    cypher = """
    MATCH (n)
    OPTIONAL MATCH (n)-[r]->(m)
    RETURN
        id(n) AS source_id, labels(n)[0] AS source_label, n AS source_data,
        type(r) AS rel_type,
        id(m) AS target_id, labels(m)[0] AS target_label, m AS target_data
    LIMIT 1000
    """
    with neo4j_driver.session() as s:
        results = s.run(cypher)
        nodes, edges = [], []
        node_ids = set()

        for record in results:
            # Traitement du nœud source
            sid = record["source_id"]
            if sid is not None and sid not in node_ids:
                d = dict(record["source_data"])
                label_type = record["source_label"]
                # --- Formatage du label selon le type ---
                if label_type == "Niveau":
                    # Priorité à la propriété 'label' (L1, L2, M1...), sinon 'rang'
                    display = d.get("label") or f"Niveau {d.get('rang', '?')}"
                elif label_type == "TypeCours":
                    typ = d.get("type", "")
                    if typ == "fondamental":
                        display = "Fondamental"
                    elif typ == "optionnel":
                        display = "Optionnel"
                    elif typ == "specialite":
                        display = "Spécialité"
                    else:
                        display = "TypeCours"
                elif label_type == "Specialite":
                    code = d.get("code", "")
                    display = f"Spé. {code}" if code else "Spécialité"
                elif label_type == "Enseignant":
                    titre = d.get("titre", "")
                    nom = d.get("nom", "")
                    display = f"{titre} {nom}".strip()
                elif label_type == "UE":
                    code = d.get("code", "")
                    intitule = d.get("intitule", "")
                    if len(intitule) > 25:
                        intitule = intitule[:22] + "..."
                    display = f"{code} - {intitule}" if code else intitule
                elif label_type == "Etudiant":
                    nom = d.get("nom", "")
                    prenom = d.get("prenom", "")
                    specialite = d.get("specialite", "")
                    if specialite:
                        display = f"{prenom} {nom} ({specialite})"
                    else:
                        display = f"{prenom} {nom}"
                elif label_type == "Departement":
                    display = d.get("nom", "Département")
                elif label_type == "Filiere":
                    display = d.get("nom", "Filière")
                else:
                    # Fallback générique
                    display = d.get("nom") or d.get("intitule") or d.get("matricule") or d.get("code") or "?"
                # --- Fin du formatage ---
                nodes.append({
                    "id": sid,
                    "label": display,
                    "group": label_type
                })
                node_ids.add(sid)

            # Traitement du nœud cible (identique)
            tid = record["target_id"]
            if tid is not None and tid not in node_ids:
                d = dict(record["target_data"])
                label_type = record["target_label"]
                # Même logique de formatage (copier-coller ou appeler une fonction locale)
                if label_type == "Niveau":
                    display = d.get("label") or f"Niveau {d.get('rang', '?')}"
                elif label_type == "TypeCours":
                    typ = d.get("type", "")
                    if typ == "fondamental":
                        display = "Fondamental"
                    elif typ == "optionnel":
                        display = "Optionnel"
                    elif typ == "specialite":
                        display = "Spécialité"
                    else:
                        display = "TypeCours"
                elif label_type == "Specialite":
                    code = d.get("code", "")
                    display = f"Spé. {code}" if code else "Spécialité"
                elif label_type == "Enseignant":
                    titre = d.get("titre", "")
                    nom = d.get("nom", "")
                    display = f"{titre} {nom}".strip()
                elif label_type == "UE":
                    code = d.get("code", "")
                    intitule = d.get("intitule", "")
                    if len(intitule) > 25:
                        intitule = intitule[:22] + "..."
                    display = f"{code} - {intitule}" if code else intitule
                elif label_type == "Etudiant":
                    nom = d.get("nom", "")
                    prenom = d.get("prenom", "")
                    specialite = d.get("specialite", "")
                    display = f"{prenom} {nom} ({specialite})" if specialite else f"{prenom} {nom}"
                elif label_type == "Departement":
                    display = d.get("nom", "Département")
                elif label_type == "Filiere":
                    display = d.get("nom", "Filière")
                else:
                    display = d.get("nom") or d.get("intitule") or d.get("matricule") or d.get("code") or "?"
                nodes.append({
                    "id": tid,
                    "label": display,
                    "group": label_type
                })
                node_ids.add(tid)

            # Ajout de la relation
            if record["rel_type"] and sid is not None and tid is not None:
                edges.append({"from": sid, "to": tid, "label": record["rel_type"]})

    return jsonify({"nodes": nodes, "edges": edges})

# ─────────────────────────────────────────────
#  Stats publiques
# ─────────────────────────────────────────────
@app.route("/api/stats")
def public_stats():
    try:
        counts = query_graph("""
            MATCH (n)
            RETURN labels(n)[0] AS type, count(n) AS total
            ORDER BY total DESC
        """)
        total_nodes = sum(r["total"] for r in counts)
        total_rels  = query_graph("MATCH ()-[r]->() RETURN count(r) AS total")[0]["total"]
        return jsonify({
            "nodes_by_type":   counts,
            "total_nodes":     total_nodes,
            "total_relations": total_rels
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ═════════════════════════════════════════════
#  AUTH ADMIN (email / mot de passe)
# ═════════════════════════════════════════════

@app.route("/admin/login", methods=["GET"])
def admin_login_page():
    return render_template("login.html")


@app.route("/admin/login", methods=["POST"])
def admin_login():
    data = request.json or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    # Vérifier si l'email est admin (super ou secondaire)
    is_super = (email == SUPER_ADMIN_EMAIL.lower())
    is_secondary = (email in ADMIN_EMAILS)

    if not (is_super or is_secondary):
        return jsonify({"success": False, "message": "Accès non autorisé"}), 401

    # Vérifier le mot de passe
    if is_super and password == SUPER_ADMIN_PASSWORD:
        token = create_access_token(identity=email)
        resp = make_response(jsonify({"success": True, "message": "Connexion réussie"}))
        set_access_cookies(resp, token)
        return resp, 200
    elif is_secondary and password == ADMIN_COMMON_PASSWORD:
        token = create_access_token(identity=email)
        resp = make_response(jsonify({"success": True, "message": "Connexion réussie"}))
        set_access_cookies(resp, token)
        return resp, 200
    else:
        return jsonify({"success": False, "message": "Email ou mot de passe incorrect"}), 401


# ═════════════════════════════════════════════
#  AUTH GOOGLE OAUTH
# ═════════════════════════════════════════════

@app.route("/auth/google")
def google_login():
    if not GOOGLE_CLIENT_ID:
        return jsonify({"error": "Google OAuth non configure. Ajoutez GOOGLE_CLIENT_ID dans .env"}), 501

    oauth = OAuth2Session(
        GOOGLE_CLIENT_ID,
        GOOGLE_CLIENT_SECRET,
        redirect_uri=GOOGLE_REDIRECT_URI,
        scope=["openid", "email", "profile"]
    )
    uri, state = oauth.create_authorization_url("https://accounts.google.com/o/oauth2/auth")
    session["oauth_state"] = state
    return redirect(uri)

@app.route("/auth/google/callback")
def google_callback():
    if not GOOGLE_CLIENT_ID:
        return jsonify({"error": "Google OAuth non configuré"}), 501

    oauth = OAuth2Session(
        GOOGLE_CLIENT_ID,
        GOOGLE_CLIENT_SECRET,
        redirect_uri=GOOGLE_REDIRECT_URI,
        state=session.get("oauth_state")
    )
    
    try:
        # 1. Récupération du token
        oauth.fetch_token(
            "https://oauth2.googleapis.com/token",
            authorization_response=request.url
        )
        
        # 2. Récupération des infos utilisateur
        userinfo = oauth.get("https://www.googleapis.com/oauth2/v3/userinfo").json()
        google_email = userinfo.get("email", "").lower()
        
        # 3. Vérification du rôle Admin
        # On compare l'email reçu avec l'ADMIN_EMAIL du fichier .env
        is_admin = (google_email in ALL_ADMIN_EMAILS)
        # 4. Création du Token JWT
        # CRUCIAL : On utilise l'email (string) comme identité pour éviter l'erreur 422
        jwt_token = create_access_token(identity=google_email)

        # 5. Redirection selon le rôle
        if is_admin:
            target_url = url_for("admin_page")
        else:
            # Si ce n'est pas l'admin, on peut rediriger vers l'index 
            # ou une page d'erreur selon ton besoin
            target_url = url_for("index")

        resp = make_response(redirect(target_url))
        
        # 6. Pose du cookie JWT
        set_access_cookies(resp, jwt_token)
        
        print(f"Connexion Google réussie pour : {google_email} (Admin: {is_admin})")
        return resp

    except Exception as e:
        print(f"Erreur callback Google : {str(e)}")
        return redirect(url_for("admin_login_page") + "?error=google_failed")

# ═════════════════════════════════════════════
#  ROUTES ADMIN PROTÉGÉES
# ═════════════════════════════════════════════

@app.route("/admin")
@admin_required
def admin_page():
    return render_template("admin.html")


@app.route("/admin/api/stats")
@admin_required
def admin_stats():
    counts    = query_graph("MATCH (n) RETURN labels(n)[0] AS type, count(n) AS total ORDER BY total DESC")
    rel_types = query_graph("MATCH ()-[r]->() RETURN type(r) AS type, count(r) AS total ORDER BY total DESC")
    return jsonify({"nodes": counts, "relations": rel_types})


@app.route("/admin/api/cluster")
@admin_required
def cluster_health():
    try:
        with neo4j_driver.session() as s:
            result  = s.run("CALL dbms.cluster.overview() YIELD id, addresses, role, database")
            servers = [dict(r) for r in result]
        return jsonify({"status": "ok", "servers": servers})
    except Exception as e:
        return jsonify({"status": "standalone", "message": str(e)})


@app.route("/admin/api/nodes/<label>")
@admin_required
def list_nodes(label):
    allowed = ["Departement", "Filiere", "Niveau", "UE", "Enseignant",
               "Etudiant", "Secretaire", "Specialite", "TypeCours"]
    if label not in allowed:
        return jsonify({"error": "Label non autorise"}), 400
    data = query_graph(f"MATCH (n:{label}) RETURN n ORDER BY n.nom LIMIT 200")
    return jsonify(data)


@app.route("/admin/api/enseignant", methods=["POST"])
@admin_required
def api_add_enseignant():
    d        = request.json or {}
    required = ["nom", "prenom", "titre", "grade", "email"]
    if not all(d.get(k) for k in required):
        return jsonify({"error": "Champs manquants : " + ", ".join(required)}), 400
    db_manager.add_enseignant(
        nom=d["nom"], prenom=d["prenom"], titre=d["titre"],
        grade=d["grade"], email=d["email"],
        photo_url=d.get("photo_url", "")
    )
    return jsonify({"message": f"Enseignant {d['titre']} {d['nom']} ajoute."})


# ========== DEPARTEMENT ==========


@app.route("/admin/api/departement", methods=["POST"])
@admin_required
def api_add_departement():
    d = request.json or {}
    if not d.get("nom") or not d.get("code"):
        return jsonify({"error": "nom et code sont obligatoires"}), 400
    db_manager.add_departement(d["nom"], d["code"], d.get("description", ""))
    return jsonify({"message": f"Departement {d['nom']} ajoute."})

@app.route("/admin/api/departements", methods=["GET"])
@admin_required
def list_departements():
    cypher = """
    MATCH (d:Departement)
    OPTIONAL MATCH (d)<-[:DIRIGE]-(e:Enseignant)
    RETURN d.code AS code,
           d.nom AS nom,
           d.description AS description,
           e.nom AS chef_nom,
           e.prenom AS chef_prenom
    ORDER BY d.nom
    """
    data = query_graph(cypher)
    return jsonify(data)

# ========== FILIERES ==========

@app.route("/admin/api/filiere", methods=["POST"])
@admin_required
def api_add_filiere():
    d = request.json or {}
    if not d.get("nom") or not d.get("code") or not d.get("dept_nom"):
        return jsonify({"error": "nom, code, dept_nom sont obligatoires"}), 400
    db_manager.add_filiere(d["nom"], d["code"], d["dept_nom"])
    return jsonify({"message": f"Filiere {d['nom']} ajoutee et liee a {d['dept_nom']}."})


@app.route("/admin/api/filieres", methods=["GET"])
@admin_required
def list_filieres():
    cypher = """
    MATCH (d:Departement)-[:CONTIENT]->(f:Filiere)
    RETURN f.code AS code,
           f.nom AS nom,
           d.nom AS departement
    ORDER BY d.nom, f.nom
    """
    data = query_graph(cypher)
    return jsonify(data)


# ==========  EU ==========


@app.route("/admin/api/ue", methods=["POST"])
@admin_required
def api_add_ue():
    d        = request.json or {}
    required = ["code", "intitule", "credits", "semestre", "type_cours", "niveau_rang", "filiere_nom"]
    if not all(d.get(k) for k in required):
        return jsonify({"error": "Champs manquants"}), 400
    db_manager.add_ue(
        code=d["code"], intitule=d["intitule"],
        credits=int(d["credits"]), semestre=int(d["semestre"]),
        type_cours=d["type_cours"],
        niveau_rang=int(d["niveau_rang"]),
        filiere_nom=d["filiere_nom"],
        specialite_nom=d.get("specialite_nom", "")
    )
    return jsonify({"message": f"UE {d['code']} ajoutee."})


@app.route("/admin/api/ues", methods=["GET"])
@admin_required
def list_ues():
    cypher = """
    MATCH (u:UE)
    OPTIONAL MATCH (u)<-[:CONTIENT_UE]-(tc:TypeCours)
    OPTIONAL MATCH (tc)-[:INCLUT_TYPE]-(n:Niveau)
    OPTIONAL MATCH (n)-[:A_NIVEAU]-(f:Filiere)
    OPTIONAL MATCH (u)<-[:ENSEIGNE]-(e:Enseignant)
    OPTIONAL MATCH (tc)-[:REGROUPE]->(sp:Specialite)
    RETURN DISTINCT
        u.code AS code,
        u.intitule AS intitule,
        u.credits AS credits,
        u.semestre AS semestre,
        u.type AS type_cours,
        f.nom AS filiere,
        n.label AS niveau_label,
        n.rang AS niveau_rang,
        sp.nom AS specialite,
        COLLECT(DISTINCT {nom: e.nom, prenom: e.prenom, titre: e.titre}) AS enseignants
    ORDER BY f.nom, n.rang, u.code
    """
    data = query_graph(cypher)
    # Transformer les enseignants en chaîne lisible
    result = []
    for row in data:
        enseignants_str = ", ".join([f"{ens['titre']} {ens['prenom']} {ens['nom']}".strip() for ens in row["enseignants"] if ens["nom"]])
        result.append({
            "code": row["code"],
            "intitule": row["intitule"],
            "credits": row["credits"],
            "semestre": row["semestre"],
            "type_cours": row["type_cours"],
            "filiere": row["filiere"] or "—",
            "niveau": f"{row['niveau_label'] or ''} (Niv.{row['niveau_rang']})" if row["niveau_rang"] else "—",
            "specialite": row["specialite"] or "—",
            "enseignants": enseignants_str or "—"
        })
    return jsonify(result)

# ==========  ENSEIGNANT ==========


@app.route("/admin/api/enseigne", methods=["POST"])
@admin_required
def api_link_enseigne():
    d = request.json or {}
    if not d.get("enseignant_nom") or not d.get("ue_code"):
        return jsonify({"error": "enseignant_nom et ue_code sont obligatoires"}), 400
    db_manager.link_enseignant_ue(d["enseignant_nom"], d["ue_code"])
    return jsonify({"message": f"{d['enseignant_nom']} lie a {d['ue_code']}."})


@app.route("/admin/api/chef", methods=["POST"])
@admin_required
def api_set_chef():
    d = request.json or {}
    if not d.get("enseignant_nom") or not d.get("dept_nom"):
        return jsonify({"error": "enseignant_nom et dept_nom obligatoires"}), 400
    db_manager.set_chef_departement(d["enseignant_nom"], d["dept_nom"])
    return jsonify({"message": f"{d['enseignant_nom']} designe chef de {d['dept_nom']}."})

# ==========  ETUDIENT ==========
@app.route("/admin/api/etudiant", methods=["POST"])
@admin_required
def api_add_etudiant():
    d = request.json or {}
    if not d.get("matricule") or not d.get("nom") or not d.get("filiere_code"):
        return jsonify({"error": "matricule, nom et filiere_code sont obligatoires"}), 400
    db_manager.add_etudiant(
        matricule=d["matricule"], nom=d["nom"], prenom=d.get("prenom", ""),
        sexe=d.get("sexe", "M"), date_naissance=d.get("date_naissance", ""),
        filiere_code=d["filiere_code"], niveau_rang=int(d.get("niveau_rang", 1))
    )
    return jsonify({"message": f"Etudiant {d['matricule']} inscrit."})


@app.route("/admin/api/etudiants", methods=["GET"])
@admin_required
def list_etudiants():
    cypher = """
    MATCH (e:Etudiant)
    OPTIONAL MATCH (e)-[:INSCRIT_DANS]->(f:Filiere)
    OPTIONAL MATCH (e)-[:EST_EN]->(n:Niveau)
    RETURN e.matricule AS matricule,
           e.nom AS nom,
           e.prenom AS prenom,
           e.sexe AS sexe,
           e.date_naissance AS date_naissance,
           f.nom AS filiere,
           n.label AS niveau_label,
           n.rang AS niveau_rang
    ORDER BY e.nom
    """
    data = query_graph(cypher)
    return jsonify(data)

@app.route("/admin/api/node/<int:node_id>", methods=["DELETE"])
@admin_required
def delete_node(node_id):
    query_graph("MATCH (n) WHERE id(n) = $nid DETACH DELETE n", {"nid": node_id})
    return jsonify({"message": f"Noeud {node_id} supprime."})


@app.route("/admin/api/clear", methods=["POST"])
@admin_required
def api_clear():
    db_manager.clear_database()
    return jsonify({"message": "Base de donnees entierement videe."})


@app.route("/admin/api/seed", methods=["POST"])
@admin_required
def api_seed():
    from ingest_data import DataIngestor
    ingestor = DataIngestor()
    ingestor.setup_database()
    ingestor.close()
    return jsonify({"message": "Donnees de demonstration chargees avec succes."})


# ═════════════════════════════════════════════
#  Vérification du token
# ═════════════════════════════════════════════

@app.route("/api/me")
@jwt_required(optional=True)
def api_me():
    identity = get_jwt_identity()
    if identity:
        is_admin = identity.lower() in ALL_ADMIN_EMAILS
        return jsonify({
            "authenticated": True,
            "user": identity,
            "role": "admin" if is_admin else "user"
        })
    return jsonify({"authenticated": False})
# ========== SECRÉTAIRES ==========
@app.route("/admin/api/secretaire", methods=["POST"])
@admin_required
def api_add_secretaire():
    d = request.json or {}
    required = ["nom", "prenom", "email", "dept_nom"]
    if not all(d.get(k) for k in required):
        return jsonify({"error": "Champs manquants : " + ", ".join(required)}), 400
    db_manager.add_secretaire(
        nom=d["nom"], prenom=d["prenom"],
        email=d["email"], dept_nom=d["dept_nom"]
    )
    return jsonify({"message": f"Secrétaire {d['prenom']} {d['nom']} ajouté au département {d['dept_nom']}."})


@app.route("/admin/api/secretaires", methods=["GET"])
@admin_required
def list_secretaires():
    cypher = """
    MATCH (s:Secretaire)-[:RATTACHEE_A]->(d:Departement)
    RETURN s.nom AS nom, s.prenom AS prenom, s.email AS email, d.nom AS departement
    """
    data = query_graph(cypher)
    return jsonify(data)

# ========== DÉLÉGUÉS ÉTUDIANTS ==========
@app.route("/admin/api/delegue", methods=["POST"])
@admin_required
def api_set_delegue():
    d = request.json or {}
    # champs: matricule, groupe, cible_nom, cible_type ("Niveau" ou "Specialite")
    required = ["matricule", "groupe", "cible_nom", "cible_type"]
    if not all(d.get(k) for k in required):
        return jsonify({"error": "matricule, groupe, cible_nom, cible_type sont obligatoires"}), 400
    if d["cible_type"] not in ["Niveau", "Specialite"]:
        return jsonify({"error": "cible_type doit être 'Niveau' ou 'Specialite'"}), 400
    
    try:
        db_manager.set_delegue(
            matricule=d["matricule"],
            groupe=d["groupe"],
            cible_nom=d["cible_nom"],
            cible_type=d["cible_type"]
        )
        return jsonify({"message": f"Étudiant {d['matricule']} nommé délégué ({d['groupe']}) pour {d['cible_type']} {d['cible_nom']}."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/admin/api/delegues", methods=["GET"])
@admin_required
def list_delegues():
    cypher = """
    MATCH (e:Etudiant)-[r:EST_DELEGUE]->(c)
    OPTIONAL MATCH (f:Filiere)-[:A_NIVEAU]->(c)
    RETURN e.matricule AS matricule,
           e.nom AS nom,
           e.prenom AS prenom,
           r.groupe AS groupe,
           CASE 
               WHEN c:Niveau THEN 'Niveau ' + toString(c.rang)
               WHEN c:Specialite THEN 'Spécialité ' + c.nom
           END AS niveau_specialite,
           COALESCE(f.nom, '') AS filiere
    """
    data = query_graph(cypher)
    result = []
    for row in data:
        result.append({
            "matricule": row["matricule"],
            "nom": row["nom"] or "",
            "prenom": row["prenom"] or "",
            "groupe": row["groupe"],
            "filiere": row["filiere"] or "—",
            "niveau_specialite": row["niveau_specialite"] or "—"
        })
    return jsonify(result)



# ========== VISUALISATION DES LIAISONS ==========
@app.route("/admin/api/enseigne_relations", methods=["GET"])
@admin_required
def list_enseigne_relations():
    cypher = """
    MATCH (e:Enseignant)-[:ENSEIGNE]->(u:UE)
    RETURN e.nom AS enseignant_nom,
           e.prenom AS enseignant_prenom,
           e.titre AS enseignant_titre,
           u.code AS ue_code,
           u.intitule AS ue_intitule
    ORDER BY e.nom, u.code
    """
    data = query_graph(cypher)
    return jsonify(data)

@app.route("/admin/api/chefs_departement", methods=["GET"])
@admin_required
def list_chefs_departement():
    cypher = """
    MATCH (d:Departement)<-[:DIRIGE]-(e:Enseignant)
    RETURN d.nom AS departement,
           e.nom AS enseignant_nom,
           e.prenom AS enseignant_prenom,
           e.titre AS enseignant_titre
    ORDER BY d.nom
    """
    data = query_graph(cypher)
    return jsonify(data)

@app.route("/admin/api/specialites", methods=["GET"])
@admin_required
def list_specialites():
    cypher = """
    MATCH (sp:Specialite)<-[:REGROUPE]-(tc:TypeCours {type:'specialite'})
    RETURN DISTINCT
        sp.code AS code,
        sp.nom AS nom,
        tc.filiere AS filiere
    ORDER BY tc.filiere, sp.nom
    """
    data = query_graph(cypher)
    # On transforme les valeurs None en "—"
    result = []
    for row in data:
        result.append({
            "code": row["code"] or "—",
            "nom": row["nom"] or "—",
            "filiere": row["filiere"] or "—"
        })
    return jsonify(result)
@app.route("/api/is_admin")
@jwt_required(optional=True)
def is_admin():
    identity = get_jwt_identity()
    if identity and identity.lower() in ALL_ADMIN_EMAILS:
        return jsonify({"is_admin": True})
    return jsonify({"is_admin": False})

@app.route('/favicon.ico')
def favicon():
    return redirect(url_for('static', filename='favicon.svg'))

if __name__ == "__main__":
    print("🚀 Serveur UNIGRAPH demarre sur http://127.0.0.1:5000")
    app.run(port=5000, debug=True)