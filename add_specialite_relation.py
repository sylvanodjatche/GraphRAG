import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"),
    auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))
)

def add_relations(tx):
    tx.run("""
        MATCH (e:Etudiant)
        MATCH (sp:Specialite {code: e.specialite})
        MERGE (e)-[:EST_SPECIALISE_DANS]->(sp)
    """)

with driver.session() as session:
    session.execute_write(add_relations)
    print("Relations EST_SPECIALISE_DANS ajoutées.")

driver.close()