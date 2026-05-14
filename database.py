"""
UNIGRAPH — Gestionnaire de base de données Neo4j
Schéma : Departement > Filiere > Niveau > TypeCours > UE
         Enseignant -[:ENSEIGNE]-> UE
         Etudiant -[:INSCRIT_DANS]-> Filiere, -[:EST_EN]-> Niveau
"""

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

    def _run(self, query, **params):
        with self.driver.session() as session:
            return session.run(query, **params).data()

    # ─────────────────────────────────────────
    #  RESET
    # ─────────────────────────────────────────
    def clear_database(self):
        self._run("MATCH (n) DETACH DELETE n")

    # ─────────────────────────────────────────
    #  DEPARTEMENT
    # ─────────────────────────────────────────
    def add_departement(self, nom, code, description=""):
        self._run("""
            MERGE (d:Departement {code: toUpper($code)})
            SET d.nom = toUpper($nom),
                d.description = $description
        """, nom=nom, code=code, description=description)

    # ─────────────────────────────────────────
    #  FILIERE
    # ─────────────────────────────────────────
    def add_filiere(self, nom, code, dept_nom):
        """Crée la filière, ses 5 niveaux et leurs TypeCours automatiquement."""
        self._run("""
            MATCH (d:Departement) WHERE toUpper(d.nom) = toUpper($dept_nom)
            MERGE (f:Filiere {code: toUpper($code)})
            SET f.nom = toUpper($nom)
            MERGE (d)-[:CONTIENT]->(f)
        """, nom=nom, code=code, dept_nom=dept_nom)

        labels = {1: "L1", 2: "L2", 3: "L3", 4: "M1", 5: "M2"}
        for rang, label in labels.items():
            self._run("""
                MATCH (f:Filiere {code: toUpper($code)})
                MERGE (n:Niveau {rang: $rang, filiere: toUpper($code)})
                SET n.label = $label
                MERGE (f)-[:A_NIVEAU]->(n)
            """, code=code, rang=rang, label=label)

            # TypeCours Fondamental pour tous les niveaux
            self._run("""
                MATCH (n:Niveau {rang: $rang, filiere: toUpper($code)})
                MERGE (tc:TypeCours {type: 'fondamental', filiere: toUpper($code), niveau_rang: $rang})
                MERGE (n)-[:INCLUT_TYPE]->(tc)
            """, rang=rang, code=code)

            # TypeCours Optionnel uniquement pour N1 et N2
            if rang <= 2:
                self._run("""
                    MATCH (n:Niveau {rang: $rang, filiere: toUpper($code)})
                    MERGE (tc:TypeCours {type: 'optionnel', filiere: toUpper($code), niveau_rang: $rang})
                    MERGE (n)-[:INCLUT_TYPE]->(tc)
                """, rang=rang, code=code)

            # TypeCours Spécialité pour N3, N4, N5
            if rang >= 3:
                self._run("""
                    MATCH (n:Niveau {rang: $rang, filiere: toUpper($code)})
                    MERGE (tc:TypeCours {type: 'specialite', filiere: toUpper($code), niveau_rang: $rang})
                    MERGE (n)-[:INCLUT_TYPE]->(tc)
                """, rang=rang, code=code)

    # ─────────────────────────────────────────
    #  SPÉCIALITÉ
    # ─────────────────────────────────────────
    def add_specialite(self, nom, code, filiere_code, niveau_rang):
        """Crée une spécialité et la lie au TypeCours 'specialite' du niveau."""
        self._run("""
            MERGE (sp:Specialite {code: toUpper($code)})
            SET sp.nom = toUpper($nom)
        """, nom=nom, code=code)

        self._run("""
            MATCH (tc:TypeCours {type: 'specialite',
                                  filiere: toUpper($filiere_code),
                                  niveau_rang: $niveau_rang})
            MATCH (sp:Specialite {code: toUpper($code)})
            MERGE (tc)-[:REGROUPE]->(sp)
        """, filiere_code=filiere_code, niveau_rang=niveau_rang, code=code)

    # ─────────────────────────────────────────
    #  UNITÉ D'ENSEIGNEMENT
    # ─────────────────────────────────────────
    def add_ue(self, code, intitule, credits, semestre,
               type_cours, niveau_rang, filiere_nom, specialite_nom=""):
        """
        type_cours : 'fondamental' | 'optionnel' | 'specialite'
        Si type_cours == 'specialite', specialite_nom doit être renseigné.
        """
        self._run("""
            MERGE (u:UE {code: toUpper($code)})
            SET u.intitule  = toUpper($intitule),
                u.credits   = $credits,
                u.semestre  = $semestre,
                u.type      = $type_cours
        """, code=code, intitule=intitule, credits=credits,
             semestre=semestre, type_cours=type_cours)

        if type_cours == "specialite" and specialite_nom:
            self._run("""
                MATCH (sp:Specialite) WHERE toUpper(sp.nom) = toUpper($specialite_nom)
                MATCH (u:UE {code: toUpper($code)})
                MERGE (sp)-[:CONTIENT_UE]->(u)
            """, specialite_nom=specialite_nom, code=code)
        else:
            self._run("""
                MATCH (tc:TypeCours {type: $type_cours,
                                      niveau_rang: $niveau_rang})
                WHERE EXISTS {
                    MATCH (:Filiere)-[:A_NIVEAU]->(:Niveau {rang: $niveau_rang})
                          -[:INCLUT_TYPE]->(tc)
                }
                MATCH (u:UE {code: toUpper($code)})
                MERGE (tc)-[:CONTIENT_UE]->(u)
            """, type_cours=type_cours, niveau_rang=niveau_rang, code=code)

    # ─────────────────────────────────────────
    #  ENSEIGNANT
    # ─────────────────────────────────────────
    def add_enseignant(self, nom, prenom, titre, grade, email, photo_url=""):
        self._run("""
            MERGE (e:Enseignant {email: toLower($email)})
            SET e.nom       = toUpper($nom),
                e.prenom    = $prenom,
                e.titre     = $titre,
                e.grade     = $grade,
                e.photo_url = $photo_url
        """, nom=nom, prenom=prenom, titre=titre,
             grade=grade, email=email, photo_url=photo_url)

    def link_enseignant_ue(self, enseignant_nom, ue_code):
        """Lie un enseignant à une UE via ENSEIGNE."""
        self._run("""
            MATCH (e:Enseignant) WHERE toUpper(e.nom) CONTAINS toUpper($nom)
            MATCH (u:UE {code: toUpper($code)})
            MERGE (e)-[:ENSEIGNE]->(u)
        """, nom=enseignant_nom, code=ue_code)

    def set_chef_departement(self, enseignant_nom, dept_nom):
        """Désigne un enseignant comme chef de département."""
        self._run("""
            MATCH (e:Enseignant) WHERE toUpper(e.nom) CONTAINS toUpper($ens_nom)
            MATCH (d:Departement) WHERE toUpper(d.nom) CONTAINS toUpper($dept_nom)
            MERGE (d)<-[:DIRIGE]-(e)
        """, ens_nom=enseignant_nom, dept_nom=dept_nom)

    # ─────────────────────────────────────────
    #  SECRÉTAIRE
    # ─────────────────────────────────────────
    def add_secretaire(self, nom, prenom, email, dept_nom):
        self._run("""
            MATCH (d:Departement) WHERE toUpper(d.nom) CONTAINS toUpper($dept_nom)
            MERGE (s:Secretaire {email: toLower($email)})
            SET s.nom    = toUpper($nom),
                s.prenom = $prenom
            MERGE (d)<-[:RATTACHEE_A]-(s)
        """, nom=nom, prenom=prenom, email=email, dept_nom=dept_nom)

    # ─────────────────────────────────────────
    #  ÉTUDIANT
    # ─────────────────────────────────────────
    def add_etudiant(self, matricule, nom, prenom, sexe,
                     date_naissance, filiere_code, niveau_rang):
        self._run("""
            MERGE (et:Etudiant {matricule: toUpper($matricule)})
            SET et.nom            = toUpper($nom),
                et.prenom         = $prenom,
                et.sexe           = $sexe,
                et.date_naissance = $date_naissance
            WITH et
            MATCH (f:Filiere {code: toUpper($filiere_code)})
            MATCH (n:Niveau {rang: $niveau_rang, filiere: toUpper($filiere_code)})
            MERGE (et)-[:INSCRIT_DANS]->(f)
            MERGE (et)-[:EST_EN]->(n)
        """, matricule=matricule, nom=nom, prenom=prenom,
             sexe=sexe, date_naissance=date_naissance,
             filiere_code=filiere_code, niveau_rang=niveau_rang)

    def set_delegue(self, matricule, groupe, cible_nom, cible_type="Niveau"):
        """
        groupe      : 'fondamental' | 'optionnel' | 'specialite:<NomSpecialite>'
        cible_type  : 'Niveau' | 'Specialite'
        cible_nom   : rang (int) pour Niveau, ou nom (str) pour Specialite
        """
        if cible_type == "Niveau":
            self._run("""
                MATCH (et:Etudiant {matricule: toUpper($matricule)})
                MATCH (n:Niveau {rang: $rang})
                MERGE (et)-[:EST_DELEGUE {groupe: $groupe}]->(n)
            """, matricule=matricule, rang=int(cible_nom), groupe=groupe)
        else:
            self._run("""
                MATCH (et:Etudiant {matricule: toUpper($matricule)})
                MATCH (sp:Specialite) WHERE toUpper(sp.nom) CONTAINS toUpper($sp_nom)
                MERGE (et)-[:EST_DELEGUE {groupe: $groupe}]->(sp)
            """, matricule=matricule, sp_nom=str(cible_nom), groupe=groupe)
