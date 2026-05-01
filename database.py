import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

class UnigraphDB:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            os.getenv("NEO4J_URI"), 
            auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))
        )

    def close(self):
        self.driver.close()

    def clear_database(self):
        """Supprime tout le graphe (Zone de danger)"""
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")

    def add_departement(self, nom, code, chef):
        query = "CREATE (d:Departement {nom: toUpper($nom), code: toUpper($code), chef: $chef})"
        with self.driver.session() as session:
            session.run(query, nom=nom, code=code, chef=chef)

    def add_filiere(self, nom, code, dept_nom):
        """Crée une filière et la lie à son département"""
        query = """
        MATCH (d:Departement) WHERE d.nom = toUpper($dept_nom)
        CREATE (f:Filiere {nom: toUpper($nom), code: toUpper($code)})
        CREATE (f)-[:APPARTIENT_A]->(d)
        """
        with self.driver.session() as session:
            session.run(query, nom=nom, code=code, dept_nom=dept_nom)

    def add_enseignant(self, nom, titre, grade, email):
        query = "CREATE (e:Enseignant {nom: toUpper($nom), titre: $titre, grade: $grade, email: $email})"
        with self.driver.session() as session:
            session.run(query, nom=nom, titre=titre, grade=grade, email=email)

    def add_cours(self, nom, code, niveau, semestre, filiere_nom, enseignant_nom, salle_nom):
        """Crée un cours et crée toutes les relations (Filiere, Enseignant, Salle)"""
        query = """
        MATCH (f:Filiere) WHERE f.nom = toUpper($filiere_nom)
        MATCH (e:Enseignant) WHERE e.nom = toUpper($enseignant_nom)
        MATCH (s:Salle) WHERE s.nom = toUpper($salle_nom)
        CREATE (c:Cours {nom: toUpper($nom), code: toUpper($code), niveau: $niveau, semestre: toInteger($semestre)})
        CREATE (c)-[:PROPOSE_DANS]->(f)
        CREATE (e)-[:ENSEIGNE]->(c)
        CREATE (c)-[:SE_DEROULE_DANS]->(s)
        """
        with self.driver.session() as session:
            session.run(query, nom=nom, code=code, niveau=niveau, semestre=semestre, 
                        filiere_nom=filiere_nom, enseignant_nom=enseignant_nom, salle_nom=salle_nom)

    def add_salle(self, nom, capacite):
        query = "CREATE (s:Salle {nom: toUpper($nom), capacite: toInteger($capacite)})"
        with self.driver.session() as session:
            session.run(query, nom=nom, capacite=capacite)

    def add_etudiant(self, matricule, nom, prenoms, cours_code):
        """Crée un étudiant et l'inscrit à un cours via son code (ex: INF4038)"""
        query = """
        MATCH (c:Cours) WHERE c.code = toUpper($cours_code)
        CREATE (e:Etudiant {matricule: toUpper($matricule), nom: toUpper($nom), prenoms: $prenoms})
        CREATE (e)-[:INSCRIT_A]->(c)
        """
        with self.driver.session() as session:
            session.run(query, matricule=matricule, nom=nom, prenoms=prenoms, cours_code=cours_code)