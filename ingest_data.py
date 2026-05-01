import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

class DataIngestor:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            os.getenv("NEO4J_URI"), 
            auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))
        )

    def close(self):
        self.driver.close()

    def setup_database(self):
        with self.driver.session() as session:
            # Nettoyage complet
            session.run("MATCH (n) DETACH DELETE n")
            
            # Création avec NORMALISATION (Majuscules pour la recherche)
            query = """
            // 1. Départements (Nom en MAJUSCULES pour faciliter la correspondance)
            CREATE (d1:Departement {nom: 'INFORMATIQUE', code: 'INF', chef: 'Dr. Aminou Halidou'})
            
            // 2. Filières
            CREATE (f1:Filiere {nom: 'ICT4D', code: 'ICT'})
            CREATE (f1)-[:APPARTIENT_A]->(d1)
            
            // 3. Enseignants
            CREATE (p1:Enseignant {nom: 'DR. TAPAMO', titre: 'Dr',grade: 'Chargé de Cours', email: 'TAPAMO@univ.cm'})
            
            // 4. Salles
            CREATE (s1:Salle {nom: 'AMPHI 500', capacite: 500})
            
            // 5. Cours (Nom normalisé sans accents et en majuscules)
            CREATE (c1:Cours {nom: 'BASE DE DONNEES DISTRIBUEES', code: 'INF4038', niveau: 'M1', semestre: 2})
            CREATE (c1)-[:PROPOSE_DANS]->(f1)
            CREATE (p1)-[:ENSEIGNE]->(c1)
            CREATE (c1)-[:SE_DEROULE_DANS]->(s1)
            
            // 6. Étudiants
            CREATE (e1:Etudiant {matricule: '22W2163', nom: 'DJATCHE-NKAMGANG', prenoms: 'Sylvano'})
            CREATE (e1)-[:INSCRIT_A]->(c1)
            """
            session.run(query)
            print("✅ Base Unigraph initialisée et normalisée (MAJUSCULES) !")

if __name__ == "__main__":
    ingestor = DataIngestor()
    ingestor.setup_database()
    ingestor.close()