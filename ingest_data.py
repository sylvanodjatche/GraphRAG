#!/usr/bin/env python3
"""
UNIGRAPH — ingest_data.py
Import des données réelles du département Informatique (UY1) fournies par l'utilisateur.
- Enseignants : liste officielle (titre, nom, prénom, grade, email, photo URL)
- Unités d’enseignement : structurées par niveau et semestre
- Règles : niveau = premier chiffre du code UE ; semestre = dernier chiffre (pair → S2, impair → S1)
- Pas de données fictives ; les étudiants seront ajoutés ultérieurement.
"""

import os
import re
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# DONNÉES FOURNIES (enseignants, UE)
# ============================================================

# Liste des enseignants (Titre, Nom, Prénom, Grade, URL, Email)
ENSEIGNANTS = [
    ("Dr", "ADAMOU", "Hamza", "Chargé de Cours", "", "hamza.adamou@facsciences-uy1.cm"),
    ("Prof", "ABESSOLO", "Ghislain", "Professeur", "https://www.google.com/imgres?q=Dr%20Abessolo%20gislain%20du%20departement%20informatique%20de%20l%27uy1&imgurl=https%3A%2F%2Fi.ytimg.com%2Fvi%2FpjcD3_t0w6M%2Fhq720.jpg%3Fsqp%3D-oaymwEhCK4FEIIDSFryq4qpAxMIARUAAAAAGAElAADIQj0AgKJD%26rs%3DAOn4CLAeGyjMyZw9KjS0Yl6FrXiDY1n7XQ&imgrefurl=https%3A%2F%2Fwww.youtube.com%2Fwatch%3Fv%3DpjcD3_t0w6M&docid=UyNWw_TLF6LniM&tbnid=_4f51QJk9trz7M&vet=12ahUKEwih_93HmLaUAxUKUkEAHWeyKnIQnPAOegQIHRAB..i&w=686&h=386&hcb=2&ved=2ahUKEwih_93HmLaUAxUKUkEAHWeyKnIQnPAOegQIHRAB", "ghislain.abessolo@facsciences-uy1.cm"),
    ("Dr", "AMINOU", "Halilou", "Chargé de Cours", "https://media.licdn.com/dms/image/v2/C5103AQEve4D8lKxD2A/profile-displayphoto-shrink_200_200/profile-displayphoto-shrink_200_200/0/1517424587392", "halidou.aminou@facsciences-uy1.cm"),
    ("Prof", "ATSA ETOUNDI", "Roger", "Professeur", "https://www.researchgate.net/profile/Atsa-Roger", "roger.atsaetoundi@facsciences-uy1.cm"),
    ("Dr", "BAYEM", "Jacques Narcisse", "Chargé de Cours", "", "jacquesnarcisse.bayem@facsciences-uy1.cm"),
    ("Dr", "BOGSO", "B", "Chargé de Cours", "", "b.bogso@facsciences-uy1.cm"),
    ("Dr", "DJAM KIMBI", "Xaveria Youhep", "Chargé de Cours", "", "xaveriayouhep.djamkimbi@facsciences-uy1.cm"),
    ("Dr", "DOMGA KOMGUEM", "Rodrigue", "Chargé de Cours", "", "rodrigue.domgakomguem@facsciences-uy1.cm"),
    ("Dr", "EBELE", "Serge", "Chargé de Cours", "", "serge.ebele@facsciences-uy1.cm"),
    ("Dr", "EKODECK", "E", "Chargé de Cours", "https://www.researchgate.net/profile/Stephane-Ekodeck", "e.ekodeck@facsciences-uy1.cm"),
    ("Dr", "ESSOMBA", "Serge", "Chargé de Cours", "", "serge.essomba@facsciences-uy1.cm"),
    ("Dr", "FOKAM", "F", "Chargé de Cours", "", "f.fokam@facsciences-uy1.cm"),
    ("Dr", "JAMO", "J", "Chargé de Cours", "", "j.jamo@facsciences-uy1.cm"),
    ("Dr", "JIOMEKONG", "Fidel Azanzi", "Chargé de Cours", "http://federated.amecse-conferences.org/wp-content/uploads/2022/05/Azanzi-Jiomekong.png", "fidelazanzi.jiomekong@facsciences-uy1.cm"),
    ("Dr", "KOUOKAM", "Etienne", "Chargé de Cours", "https://www.researchgate.net/profile/Etienne-Kouokam", "etienne.kouokam@facsciences-uy1.cm"),
    ("Dr", "MAKEMBE", "S. Oswald", "Chargé de Cours", "", "soswald.makembe@facsciences-uy1.cm"),
    ("Dr", "MBIAKOP", "Hilaire George", "Chargé de Cours", "", "hilairegeorge.mbiakop@facsciences-uy1.cm"),
    ("Me", "MEFOUMA", "Christine", "Chargé de Cours", "", "christine.mefouma@facsciences-uy1.cm"),
    ("Prof", "MELATAGIA YONTA", "Paulin", "Professeur", "https://afriquemagazine.com/sites/default/files/inline-images/AFRIQUE-MAGAZINE-471-472-20251208-32-47.pdf-image-030.jpg", "paulin.melagiayonta@facsciences-uy1.cm"),
    ("Dr", "MESSI NGUELE", "Thomas", "Chargé de Cours", "https://media.licdn.com/dms/image/v2/C5603AQGEEg6siMWldA/profile-displayphoto-shrink_200_200/profile-displayphoto-shrink_200_200/0/1544459062923", "thomas.messinguele@facsciences-uy1.cm"),
    ("Dr", "MONTHE", "Valery", "Chargé de Cours", "https://media.licdn.com/dms/image/v2/C4E03AQGammYYMlM6AA/profile-displayphoto-shrink_200_200/profile-displayphoto-shrink_200_200/0/1516968294247", "valery.monthe@facsciences-uy1.cm"),
    ("Prof", "NDOUNDAM", "Rene", "Professeur", "https://www.researchgate.net/profile/Rene-Ndoundam", "rene.ndoundam@facsciences-uy1.cm"),
    ("Dr", "NKONDOCK BAHANACK", "N", "Chargé de Cours", "", "n.nkondockbahanack@facsciences-uy1.cm"),
    ("Dr", "NZEKON", "Armel", "Chargé de Cours", "https://www.researchgate.net/profile/Armel-Jacques-Nzekon-Nzekoo", "armel.nzekon@facsciences-uy1.cm"),
    ("Dr", "OGADOA", "O", "Chargé de Cours", "", "o.ogadoa@facsciences-uy1.cm"),
    ("Dr", "TAPAMO", "Hyppolite", "Chargé de Cours", "https://lookaside.fbsbx.com/lookaside/crawler/media/?media_id=986581356848532", "hyppolite.tapamo@facsciences-uy1.cm"),
    ("Dr", "TCHOUNDJA", "Edgar Landry", "Chargé de Cours", "", "edgarlandry.tchoundja@facsciences-uy1.cm"),
    ("Prof", "TSOPZE", "Norbert", "Professeur", "https://aims-senegal.org/wp-content/uploads/sites/2/2021/03/image38.jpg", "norbert.tsopze@facsciences-uy1.cm"),
]

# Structure des UE (extraite des tableaux fournis)
# Clé : (niveau, semestre) -> liste d'UE
# Chaque UE : dict avec code, intitule, credits, category, specialite (optionnel), enseignants (liste de noms complets)
UE_PAR_NIVEAU_SEMESTRE = {
    (1, 1): [  # L1 S1
        {"code": "INF111", "intitule": "INTRODUCTION À L'ALGORITHMIQUE ET À LA PROGRAMMATION", "credits": 6, "category": "Fondamental", "specialite": None, "enseignants": ["ATSA ETOUNDI Roger", "TSOPZE Norbert"]},
        {"code": "INF121", "intitule": "INTRODUCTION À L'ARCHITECTURE DES ORDINATEURS", "credits": 6, "category": "Fondamental", "specialite": None, "enseignants": ["KOUOKAM Etienne", "AMINOU Halilou"]},
        {"code": "INF131", "intitule": "INTRODUCTION AUX SYSTÈMES ET RÉSEAUX", "credits": 6, "category": "Fondamental", "specialite": None, "enseignants": ["DOMGA KOMGUEM Rodrigue", "ADAMOU Hamza"]},
        {"code": "MAT131", "intitule": "ANALYSE DE LA DROITE REELLE", "credits": 6, "category": "Fondamental", "specialite": None, "enseignants": ["BOGSO B", "TCHOUNDJA Edgar Landry"]},
        {"code": "FBL111", "intitule": "FORMATION BILINGUE I", "credits": 3, "category": "Optionnel", "specialite": None, "enseignants": ["ESSOMBA Serge"]},
        {"code": "INF141", "intitule": "INTRODUCTION À LA SÉCURITÉ INFORMATIQUE", "credits": 3, "category": "Optionnel", "specialite": None, "enseignants": ["EKODECK E", "EBELE Serge"]},
        {"code": "PPE111", "intitule": "EXPLORATION PROFESSIONNELLE, ORIENTATION ET EDUCATION A LA CITOYENETE", "credits": 3, "category": "Optionnel", "specialite": None, "enseignants": ["MEFOUMA Christine"]},
    ],
    (1, 2): [  # L1 S2
        {"code": "INF112", "intitule": "INTRODUCTION AUX STRUCTURES DE DONNEES", "credits": 6, "category": "Fondamental", "specialite": None, "enseignants": ["AMINOU Halilou", "MESSI NGUELE Thomas"]},
        {"code": "INF122", "intitule": "FONDEMENTS MATHEMATIQUES DE L'INFORMATIQUE", "credits": 6, "category": "Fondamental", "specialite": None, "enseignants": ["KOUOKAM Etienne", "NZEKON Armel"]},
        {"code": "INFO132", "intitule": "PROGRAMMATION STRUCTUREE EN C", "credits": 6, "category": "Fondamental", "specialite": None, "enseignants": ["TSOPZE Norbert", "TAPAMO Hyppolite"]},
        {"code": "INFO142", "intitule": "INTRODUCTION À LA SCIENCE DES DONNÉES", "credits": 3, "category": "Fondamental", "specialite": None, "enseignants": ["MELATAGIA YONTA Paulin", "NZEKON Armel"]},
        {"code": "MAT112", "intitule": "ALGEBRE 1B", "credits": 6, "category": "Fondamental", "specialite": None, "enseignants": ["OGADOA O"]},
        {"code": "INFO152", "intitule": "INTRODUCTION AU RESEAU INFORMATIQUE ET SYSTEME D’EXPLOITATION", "credits": 6, "category": "Fondamental", "specialite": None, "enseignants": ["ADAMOU Hamza", "DOMGA KOMGUEM Rodrigue"]},
    ],
    (2, 1): [  # L2 S1
        {"code": "FBL211", "intitule": "FORMATION BILINGUE II", "credits": 3, "category": "Optionnel", "specialite": None, "enseignants": ["ESSOMBA Serge"]},
        {"code": "INF211", "intitule": "PROGRAMMATION ORIENTÉE OBJET", "credits": 6, "category": "Fondamental", "specialite": None, "enseignants": ["ABESSOLO Ghislain", "JIOMEKONG Fidel Azanzi"]},
        {"code": "INF221", "intitule": "BASES DE DONNEES ET MODELISATION", "credits": 6, "category": "Fondamental", "specialite": None, "enseignants": ["ABESSOLO Ghislain", "KOUOKAM Etienne"]},
        {"code": "INF231", "intitule": "METHODES ALGORITHMIQUES ET STRUCTURES DE DONNEES", "credits": 6, "category": "Fondamental", "specialite": None, "enseignants": ["TAPAMO Hyppolite", "MESSI NGUELE Thomas"]},
        {"code": "MAT211", "intitule": "ALGEBRE 2A : THEORIE SPECTRALE ET ALGEBRE MULTILINEAIRE", "credits": 6, "category": "Fondamental", "specialite": None, "enseignants": ["MBIAKOP Hilaire George", "OGADOA O"]},
        {"code": "INF251", "intitule": "GENIE LOGICIEL ET SYSTEMES D'INFORMATION", "credits": 6, "category": "Fondamental", "specialite": None, "enseignants": ["BAYEM Jacques Narcisse", "ABESSOLO Ghislain", "NKONDOCK BAHANACK N"]},
    ],
    (2, 2): [  # L2 S2
        {"code": "INF222", "intitule": "PROGRAMMATION WEB", "credits": 6, "category": "Fondamental", "specialite": None, "enseignants": ["MESSI NGUELE Thomas", "JIOMEKONG Fidel Azanzi"]},
        {"code": "INF232", "intitule": "STATISTIQUES ET ANALYSE DE DONNEES", "credits": 6, "category": "Fondamental", "specialite": None, "enseignants": ["MAKEMBE S. Oswald", "NZEKON Armel"]},
        {"code": "INF212", "intitule": "MATHEMATIQUES DISCRETES", "credits": 6, "category": "Fondamental", "specialite": None, "enseignants": ["NDOUNDAM Rene"]},
        {"code": "INF242", "intitule": "SCIENCE DES DONNEES", "credits": 6, "category": "Fondamental", "specialite": None, "enseignants": ["MELATAGIA YONTA Paulin", "MESSI NGUELE Thomas"]},
        {"code": "INF252", "intitule": "SECURITE INFORMATIQUE", "credits": 6, "category": "Fondamental", "specialite": None, "enseignants": ["NKONDOCK BAHANACK N", "BAYEM Jacques Narcisse"]},
        {"code": "PPE212", "intitule": "PROJET PROFESSIONNEL ET PRE-IMMERSION", "credits": 3, "category": "Fondamental", "specialite": None, "enseignants": ["TAPAMO Hyppolite", "MEFOUMA Christine"]},
        {"code": "MAT232", "intitule": "CALCUL INTEGRAL SUR R^n", "credits": 6, "category": "Fondamental", "specialite": None, "enseignants": ["FOKAM F"]},
    ],
    (3, 1): [  # L3 S1
        {"code": "ENG311", "intitule": "FORMATION BILINGUE 3", "credits": 3, "category": "Optionnel", "specialite": None, "enseignants": ["ESSOMBA Serge"]},
        {"code": "FRA311", "intitule": "FORMATION BILINGUE 3", "credits": 3, "category": "Optionnel", "specialite": None, "enseignants": ["JAMO J"]},
        {"code": "INF311", "intitule": "CALCUL SCIENTIFIQUE", "credits": 6, "category": "Fondamental", "specialite": None, "enseignants": ["NZEKON Armel"]},
        {"code": "INF312", "intitule": "ANALYSES STATISTIQUES", "credits": 6, "category": "Fondamental", "specialite": None, "enseignants": ["NZEKON Armel"]},
    ],
    (3, 2): [  # L3 S2
        {"code": "INF321", "intitule": "CONCEPTION ET ANALYSE DES ALGORITHMES", "credits": 6, "category": "Fondamental", "specialite": None, "enseignants": ["MESSI NGUELE Thomas"]},
        {"code": "INF322", "intitule": "BASE DE DONNEES", "credits": 6, "category": "Fondamental", "specialite": None, "enseignants": ["MONTHE Valery"]},
        {"code": "INF331", "intitule": "MODELISATION DU SYSTEME D’INFORMATION", "credits": 6, "category": "Fondamental", "specialite": None, "enseignants": ["MONTHE Valery"]},
        {"code": "INF332", "intitule": "INTRODUCTION A LA THEORIE DES CODES", "credits": 6, "category": "Fondamental", "specialite": None, "enseignants": ["EKODECK E"]},
        {"code": "INF341", "intitule": "RESEAUX LOCAUX", "credits": 6, "category": "Fondamental", "specialite": None, "enseignants": ["AMINOU Halilou", "DOMGA KOMGUEM Rodrigue"]},
        {"code": "INF342", "intitule": "THEORIE DES LANGAGES ET COMPILATION", "credits": 6, "category": "Fondamental", "specialite": None, "enseignants": ["KOUOKAM Etienne", "MESSI NGUELE Thomas"]},
        {"code": "INF371", "intitule": "INFORMATIQUE DECISIONNELLE ET FOUILLE DE DONNÉES", "credits": 6, "category": "Spécialité", "specialite": "SD", "enseignants": ["TSOPZE Norbert", "MELATAGIA YONTA Paulin"]},
        {"code": "PPE312", "intitule": "PROJET PROFESSIONNEL DE L'ETUDIANT III", "credits": 6, "category": "Fondamental", "specialite": None, "enseignants": []},
    ],
    (4, 1): [  # M1 S1
        {"code": "INF4017", "intitule": "COMPLEXITÉ ET ALGORITHMIQUE AVANCÉE", "credits": 6, "category": "Fondamental", "specialite": None, "enseignants": ["NDOUNDAM Rene"]},
        {"code": "INF4027", "intitule": "GÉNIE LOGICIEL", "credits": 6, "category": "Fondamental", "specialite": None, "enseignants": ["ATSA ETOUNDI Roger"]},
        {"code": "INF4057", "intitule": "ARCHITECTURES LOGICIELLES", "credits": 6, "category": "Spécialité", "specialite": "GL", "enseignants": ["DJAM KIMBI Xaveria Youhep"]},
        {"code": "INF4067", "intitule": "UML ET DESIGN PATTERNS", "credits": 6, "category": "Spécialité", "specialite": "GL", "enseignants": ["MONTHE Valery"]},
        {"code": "INF4077", "intitule": "PROGRAMMATION DES TERMINAUX MOBILES", "credits": 6, "category": "Spécialité", "specialite": "GL", "enseignants": ["JIOMEKONG Fidel Azanzi"]},
        {"code": "INF4087", "intitule": "RÉSEAUX II", "credits": 6, "category": "Spécialité", "specialite": "SR", "enseignants": ["AMINOU Halilou"]},
        {"code": "INF4097", "intitule": "PRINCIPES DE CONCEPTION DES SYSTÈMES D'EXPLOITATION", "credits": 6, "category": "Spécialité", "specialite": "SR", "enseignants": ["ADAMOU Hamza"]},
        {"code": "INF4107", "intitule": "CLOUD COMPUTING", "credits": 6, "category": "Spécialité", "specialite": "SR", "enseignants": ["MONTHE Valery"]},
        {"code": "INF4117", "intitule": "FOUILLE DE DONNÉES II", "credits": 6, "category": "Spécialité", "specialite": "SD", "enseignants": ["TSOPZE Norbert"]},
        {"code": "INF4127", "intitule": "TECHNIQUES D'OPTIMISATION II", "credits": 6, "category": "Spécialité", "specialite": "SD", "enseignants": ["MELATAGIA YONTA Paulin"]},
        {"code": "INF4137", "intitule": "ANALYSE DES DONNÉES", "credits": 6, "category": "Spécialité", "specialite": "SD", "enseignants": ["NZEKON Armel"]},
        {"code": "INF4147", "intitule": "SÉCURITÉ INFORMATIQUE", "credits": 6, "category": "Spécialité", "specialite": "SE", "enseignants": ["EBELE Serge"]},
        {"code": "INF4157", "intitule": "SÉCURITÉ LOGICIELLE", "credits": 6, "category": "Spécialité", "specialite": "GL", "enseignants": ["DJAM KIMBI Xaveria Youhep"]},
        {"code": "INF4167", "intitule": "CRYPTOGRAPHIE SYMÉTRIQUE", "credits": 6, "category": "Spécialité", "specialite": "SE", "enseignants": ["EBELE Serge"]},
    ],
    (4, 2): [  # M1 S2
        {"code": "INF4038", "intitule": "BASE DE DONNÉES DISTRIBUÉES", "credits": 6, "category": "Fondamental", "specialite": None, "enseignants": ["TAPAMO Hyppolite"]},
        {"code": "INF4048", "intitule": "COMPILATION", "credits": 6, "category": "Fondamental", "specialite": None, "enseignants": ["KOUOKAM Etienne", "MESSI NGUELE Thomas"]},
        {"code": "INF4178", "intitule": "GÉNIE LOGICIEL I", "credits": 6, "category": "Spécialité", "specialite": "GL", "enseignants": ["DJAM KIMBI Xaveria Youhep"]},
        {"code": "INF4188", "intitule": "WEB SÉMANTIQUE ET APPLICATIONS", "credits": 6, "category": "Spécialité", "specialite": "GL", "enseignants": ["JIOMEKONG Fidel Azanzi"]},
        {"code": "INF4198", "intitule": "PROJET II", "credits": 6, "category": "Spécialité", "specialite": "GL", "enseignants": ["JIOMEKONG Fidel Azanzi"]},
        {"code": "INF4208", "intitule": "RÉSEAUX MOBILES ET SANS FILS", "credits": 6, "category": "Spécialité", "specialite": "SR", "enseignants": ["DOMGA KOMGUEM Rodrigue"]},
        {"code": "INF4218", "intitule": "PROGRAMMATION DISTRIBUÉE", "credits": 6, "category": "Spécialité", "specialite": "SR", "enseignants": ["ADAMOU Hamza"]},
        {"code": "INF4228", "intitule": "PROJET II", "credits": 6, "category": "Spécialité", "specialite": "SR", "enseignants": ["AMINOU Halilou"]},
        {"code": "INF4238", "intitule": "VISION PAR ORDINATEUR", "credits": 6, "category": "Spécialité", "specialite": "SD", "enseignants": ["TAPAMO Hyppolite"]},
        {"code": "INF4248", "intitule": "APPRENTISSAGE ARTIFICIEL II", "credits": 6, "category": "Spécialité", "specialite": "SD", "enseignants": ["MELATAGIA YONTA Paulin"]},
        {"code": "INF4258", "intitule": "PROJET II", "credits": 6, "category": "Spécialité", "specialite": "SD", "enseignants": ["TSOPZE Norbert"]},
        {"code": "INF4268", "intitule": "CRYPTOGRAPHIE ASYMÉTRIQUE", "credits": 6, "category": "Spécialité", "specialite": "SE", "enseignants": ["EKODECK E"]},
        {"code": "INF4278", "intitule": "COURBES ELLIPTIQUES 1", "credits": 6, "category": "Spécialité", "specialite": "SE", "enseignants": ["NDOUNDAM Rene"]},
        {"code": "INF4288", "intitule": "PROJET II", "credits": 6, "category": "Spécialité", "specialite": "SE", "enseignants": ["EBELE Serge"]},
    ],
}

# ============================================================
# CLASSE D'INGESTION
# ============================================================

class DataIngestor:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            os.getenv("NEO4J_URI"),
            auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))
        )
        self.enseignants_cache = {}  # {nom_complet_normalisé: (nom, prenom, email)}
        self.specialites = set()

    def close(self):
        self.driver.close()

    def _run(self, query, **params):
        with self.driver.session() as session:
            return session.run(query, **params).data()

    # ------------------- STRUCTURE DE BASE -------------------
    def create_departement(self):
        print("🏛️ Création du département INFORMATIQUE...")
        self._run("""
            CREATE (d:Departement {
                nom: 'INFORMATIQUE',
                code: 'INF',
                description: "Département d'Informatique de la Faculté des Sciences, Université de Yaoundé I"
            })
        """)
        return "INF"

    def create_filiere(self, dept_code):
        print("📚 Création de la filière INFORMATIQUE...")
        self._run("""
            MATCH (d:Departement {code: $dept_code})
            CREATE (f:Filiere {nom: 'INFORMATIQUE', code: 'INFO'})
            CREATE (d)-[:CONTIENT]->(f)
        """, dept_code=dept_code)
        labels = {1:"L1", 2:"L2", 3:"L3", 4:"M1", 5:"M2"}
        for rang, label in labels.items():
            self._run("""
                MATCH (f:Filiere {code: 'INFO'})
                CREATE (n:Niveau {rang: $rang, label: $label, filiere: 'INFO'})
                CREATE (f)-[:A_NIVEAU]->(n)
            """, rang=rang, label=label)
            # TypeCours fondamental
            self._run("""
                MATCH (n:Niveau {rang: $rang, filiere: 'INFO'})
                CREATE (tc:TypeCours {type: 'fondamental', filiere: 'INFO', niveau_rang: $rang})
                CREATE (n)-[:INCLUT_TYPE]->(tc)
            """, rang=rang)
            # TypeCours optionnel
            self._run("""
                MATCH (n:Niveau {rang: $rang, filiere: 'INFO'})
                CREATE (tc:TypeCours {type: 'optionnel', filiere: 'INFO', niveau_rang: $rang})
                CREATE (n)-[:INCLUT_TYPE]->(tc)
            """, rang=rang)
            # TypeCours spécialité (à partir de L3)
            if rang >= 3:
                self._run("""
                    MATCH (n:Niveau {rang: $rang, filiere: 'INFO'})
                    CREATE (tc:TypeCours {type: 'specialite', filiere: 'INFO', niveau_rang: $rang})
                    CREATE (n)-[:INCLUT_TYPE]->(tc)
                """, rang=rang)

    # ------------------- ENSEIGNANTS -------------------
    def add_enseignant(self, titre, nom, prenom, grade, photo_url, email):
        nom = nom.strip().upper()
        prenom = prenom.strip()
        self._run("""
            MERGE (e:Enseignant {email: toLower($email)})
            SET e.nom = $nom,
                e.prenom = $prenom,
                e.titre = $titre,
                e.grade = $grade,
                e.photo_url = $photo_url
        """, nom=nom, prenom=prenom, titre=titre, grade=grade, email=email, photo_url=photo_url or "")
        # Cache pour recherche ultérieure
        key = f"{nom} {prenom}".strip().upper()
        self.enseignants_cache[key] = (nom, prenom, email)
        return key

    def load_teachers(self):
        print("👨‍🏫 Chargement des enseignants...")
        for titre, nom, prenom, grade, url, email in ENSEIGNANTS:
            self.add_enseignant(titre, nom, prenom, grade, url, email)
        print(f"   → {len(self.enseignants_cache)} enseignants chargés.")

    def find_teacher_by_name(self, nom_complet):
        """Retourne (nom, prenom, email) à partir d'un nom complet (ex: 'ATSA ETOUNDI Roger')"""
        # Normalisation : supprimer les accents, mettre en majuscules
        nom_complet = nom_complet.strip().upper()
        # On cherche une correspondance dans le cache
        # Essai exact
        if nom_complet in self.enseignants_cache:
            return self.enseignants_cache[nom_complet]
        # Essai en inversant prénom/nom (parfois le prénom est en premier)
        parts = nom_complet.split()
        if len(parts) >= 2:
            alt_key = f"{parts[-1]} {' '.join(parts[:-1])}".strip().upper()
            if alt_key in self.enseignants_cache:
                return self.enseignants_cache[alt_key]
        # Recherche floue simple
        for key in self.enseignants_cache:
            if nom_complet in key or key in nom_complet:
                return self.enseignants_cache[key]
        print(f"   ⚠️ Enseignant non trouvé : {nom_complet}")
        return None

    # ------------------- SPÉCIALITÉS -------------------
    def collect_specialites(self):
        for (niveau, semestre), ues in UE_PAR_NIVEAU_SEMESTRE.items():
            for ue in ues:
                if ue.get("specialite"):
                    self.specialites.add(ue["specialite"])
        print(f"🎓 Spécialités détectées : {self.specialites}")

    def create_specialites(self):
        for sp_code in self.specialites:
            nom = sp_code
            if sp_code == "SD":
                nom = "SCIENCE DES DONNÉES"
            elif sp_code == "GL":
                nom = "GÉNIE LOGICIEL"
            elif sp_code == "SR":
                nom = "RÉSEAUX ET SYSTÈMES"
            elif sp_code == "SE":
                nom = "SÉCURITÉ"
            self._run("""
                MERGE (sp:Specialite {code: $code})
                SET sp.nom = $nom
            """, code=sp_code, nom=nom)
        print("   ✅ Spécialités créées.")

    # ------------------- UNITÉS D'ENSEIGNEMENT -------------------
    def create_ue(self, code, intitule, credits, semestre, type_cours, niveau_rang, specialite_code=None):
        self._run("""
            MERGE (u:UE {code: toUpper($code)})
            SET u.intitule = toUpper($intitule),
                u.credits = $credits,
                u.semestre = $semestre,
                u.type = $type_cours
        """, code=code, intitule=intitule, credits=credits, semestre=semestre, type_cours=type_cours)
        # Rattachement au TypeCours correspondant
        self._run("""
            MATCH (tc:TypeCours {type: $type_cours, filiere: 'INFO', niveau_rang: $niveau_rang})
            MATCH (u:UE {code: toUpper($code)})
            MERGE (tc)-[:CONTIENT_UE]->(u)
        """, type_cours=type_cours, niveau_rang=niveau_rang, code=code)
        if specialite_code:
            self._run("""
                MATCH (sp:Specialite {code: $sp_code})
                MATCH (u:UE {code: toUpper($code)})
                MERGE (sp)-[:CONTIENT_UE]->(u)
            """, sp_code=specialite_code, code=code)

    def link_teacher_to_ue(self, teacher_tuple, ue_code):
        if not teacher_tuple:
            return
        nom, prenom, email = teacher_tuple
        self._run("""
            MATCH (e:Enseignant {nom: $nom, prenom: $prenom})
            MATCH (u:UE {code: toUpper($code)})
            MERGE (e)-[:ENSEIGNE]->(u)
        """, nom=nom, prenom=prenom, code=ue_code)

    def process_ues(self):
        print("📖 Création des Unités d'Enseignement...")
        ue_count = 0
        for (niveau_rang, semestre), ues in UE_PAR_NIVEAU_SEMESTRE.items():
            for ue in ues:
                code = ue["code"]
                intitule = ue["intitule"]
                credits = ue["credits"]
                category = ue["category"]
                specialite = ue.get("specialite")
                # Déterminer type_cours
                if specialite:
                    type_cours = "specialite"
                else:
                    if category.lower() == "fondamental":
                        type_cours = "fondamental"
                    elif category.lower() == "optionnel":
                        type_cours = "optionnel"
                    else:
                        type_cours = "fondamental"  # fallback
                self.create_ue(code, intitule, credits, semestre, type_cours, niveau_rang, specialite)
                # Lier les enseignants
                for nom_complet in ue.get("enseignants", []):
                    teacher = self.find_teacher_by_name(nom_complet)
                    if teacher:
                        self.link_teacher_to_ue(teacher, code)
                ue_count += 1
        print(f"   → {ue_count} UE créées.")

    # ------------------- MAINTENANCE -------------------
    def clear_database(self):
        print("🗑️ Nettoyage de la base...")
        self._run("MATCH (n) DETACH DELETE n")

    def set_chef_departement(self):
        print("👑 Désignation du chef de département (AMINOU Halilou)...")
        self._run("""
            MATCH (e:Enseignant {nom: 'AMINOU', prenom: 'Halilou'})
            MATCH (d:Departement {code: 'INF'})
            MERGE (d)<-[:DIRIGE]-(e)
        """)

    def add_demo_secretaires(self):
        print("👩‍💼 Ajout de secrétaires (données réelles ? fictives minimales)...")
        self._run("""
            MATCH (d:Departement {code:'INF'})
            CREATE (s1:Secretaire {nom:'NKOUDOU', prenom:'Marie-Claire', email:'nkoudou@uy1.cm'})
            CREATE (s2:Secretaire {nom:'MBALLA', prenom:'Pauline', email:'mballa@uy1.cm'})
            CREATE (s1)-[:RATTACHEE_A]->(d)
            CREATE (s2)-[:RATTACHEE_A]->(d)
        """)

    # ------------------- EXECUTION -------------------
    def run(self):
        self.clear_database()
        dept_code = self.create_departement()
        self.create_filiere(dept_code)
        self.load_teachers()
        self.collect_specialites()
        self.create_specialites()
        self.process_ues()
        self.set_chef_departement()
        self.add_demo_secretaires()
        print("\n✅ Import terminé avec succès.")
        print("   Aucun étudiant n’a été ajouté (vous les insérerez plus tard).")

if __name__ == "__main__":
    ingestor = DataIngestor()
    ingestor.run()
    ingestor.close()