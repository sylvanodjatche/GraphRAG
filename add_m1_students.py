#!/usr/bin/env python3
"""
Ajout des étudiants de Master 1 (M1) en informatique
Spécialités : GL, SR, SE, SD
Données incluant sexe et date de naissance par défaut '2000-01-01'
"""

import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"),
    auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))
)

# Structure des étudiants : (nom, prenom, matricule, sexe, specialite)
ETUDIANTS = [
    # GL (42 étudiants)
    ("ANOU NJIAZA", "Vanelle Raïssa", "22U2089", "F", "GL"),
    ("BETINE PUGUEU", "Audrey Grâce Albane", "19M2616", "F", "GL"),
    ("BIYIHA MATIMBHE", "Noe Melody", "20U2743", "M", "GL"),
    ("BOUOGNONG MOUOPE", "Stefan", "23V2626", "M", "GL"),
    ("CHENJO LEUGUEUN DE", "Prosper", "21K2995", "M", "GL"),
    ("DEUDJIE MBADI", "Sabine Axelle", "19M2144", "F", "GL"),
    ("DJAHA TCHESSEU", "Yvanna", "22U2071", "F", "GL"),
    ("DJAPANA TINDI", "Claire Ornela", "21T2438", "F", "GL"),
    ("DJIMELI TCHINDA", "Ariane", "22W2171", "F", "GL"),
    ("DJOTIO SOUFFO", "Jason Steven", "21T2706", "M", "GL"),
    ("EBAI BATE", "Lucky Betty", "21T2336", "F", "GL"),
    ("ETUGE", "Derick Etoe", "10U0064", "M", "GL"),
    ("FOGUEM JUNIOR", "Kieran", "22U2095", "M", "GL"),
    ("FOTSO BOPDA", "Achille Jordan", "22T2961", "M", "GL"),
    ("Hassane", "Badama", "19M2574", "M", "GL"),
    ("HEIL TCHAMBA", "Nana", "21T2380", "M", "GL"),
    ("KAMDEM FOSSO", "Emile Cabrel", "22T2263", "M", "GL"),
    ("KAMDEM WANDJI", "Idriss Geslain", "22T2909", "M", "GL"),
    ("KEJEWE", "David", "20U2876", "M", "GL"),
    ("KOMADJOU TCHAPTCHE", "Imelda Shelvie", "22T2956", "F", "GL"),
    ("LEUDJEU WOUAPPI", "Beautrel Horssel", "22U2079", "M", "GL"),
    ("MAAMOC KENGUIM", "Ronel", "22T2942", "M", "GL"),
    ("MAFFO NGALEU", "Laetitia", "21T2413", "F", "GL"),
    ("MBANDA PAMBI", "Naomi Pascale", "22T2900", "F", "GL"),
    ("MBENOUN TITI", "Jean Luc Dimitri", "21Y332", "M", "GL"),
    ("MENGUE", "Michel Xavier", "24F2486", "M", "GL"),
    ("Meyie Souaïbou", "Esther Yolande", "0000000", "F", "GL"),
    ("MIKAM DEUGWE", "Tracy-Jolica", "22Y1035", "F", "GL"),
    ("Mimche Moluh", "Ishak Nazir", "21T2466", "M", "GL"),
    ("MISSAKO BELL", "Joyce Cindy", "21T2445", "F", "GL"),
    ("MOKO MOTHO", "Péguy", "15T2780", "F", "GL"),
    ("NDOGA NDOGA", "Michel Blaise", "15U2896", "M", "GL"),
    ("NDONGWOU", "Florinda Laure", "22T2835", "F", "GL"),
    ("NGOGANG TCHATCHOUANG", "Andy Brayan", "21Y116", "M", "GL"),
    ("NGUEMBU YEPMO", "John Jaures", "21T2364", "M", "GL"),
    ("Ossene A koung", "Juliano Raphaël", "21T2302", "M", "GL"),
    ("TAGNY TAGNY", "Idriss Lerich", "21T2342", "M", "GL"),
    ("TIOMELA ZANGUE", "Jorel", "21U2144", "M", "GL"),
    ("TOUKAP NGANSOP", "Rayan Ledoux", "22U2142", "M", "GL"),
    ("TSABENG", "Delphan", "22U2109", "M", "GL"),
    ("WELYANG", "Foumkreo", "25G2052", "M", "GL"),
    ("WOUATCHOU SANDJON", "Fortuney Yves", "22T2922", "M", "GL"),

    # SR (9 étudiants)
    ("WATO MABOU", "Paul", "22T2920", "M", "SR"),
    ("MFENJOU ANAS", "Chérif", "21T2330", "M", "SR"),
    ("HEUKOU TCHIKAMEN", "Ingrid Noël", "25G2053", "F", "SR"),
    ("WABO POKA", "Rick Junior", "22U2175", "M", "SR"),
    ("LANGOUL", "FADILA MARIAMA Mouira", "21T2528", "M", "SR"),
    ("POLLA MARC", "Pharel", "22U2681", "M", "SR"),
    ("MEFIRE OUMAR", "Chawil", "22U2196", "M", "SR"),
    ("EDU GUIEDI", "Hermann Arnold", "22T2876", "M", "SR"),
    ("SAKTA NZIA", "Pierrick Miguel", "22Y1042", "M", "SR"),

    # SE (13 étudiants)
    ("KEMAJOU KOUAGO", "Steve Anderson", "21T2640", "M", "SE"),
    ("MAHACHU FONGANG", "Aurélie Graciane", "22T2924", "F", "SE"),
    ("NGUEUDJANG DJOMO", "Alain Gildas", "22W2183", "M", "SE"),
    ("ESSIMBI MBALLA", "Gabrielle", "22U2019", "F", "SE"),
    ("KOUGOUM FOTSING", "Pavel", "21T2887", "M", "SE"),
    ("FOTSING KENGNE", "Diane Iris", "17T2631", "F", "SE"),
    ("NINGAHE SIMON", "Pierre", "21T2832", "M", "SE"),
    ("TSAHUI NEMBOT CHRIST", "Socrate", "25G2059", "M", "SE"),
    ("ONGONO MVEME", "Bertrand", "09U0529", "M", "SE"),
    ("TADJUIDJE KAMDEM", "André Jordan", "21T2472", "M", "SE"),
    ("MALIEDJE CHOUPO", "Jasmine Raïssa", "21T2411", "F", "SE"),
    ("TAHUE TCHOUTCHOUA", "Gemaël Dimitri", "25G2032", "M", "SE"),
    ("DONGMO NGATSI", "Reine", "21U2391", "F", "SE"),

    # SD (36 étudiants)
    ("BELL ARSENE", "Kevin", "22T2960", "M", "SD"),
    ("BIBOUE LIMALEBA", "Stephane", "19U2997", "M", "SD"),
    ("BOKOU-BOUNA", "Ange Larissa", "22W2188", "F", "SD"),
    ("CHEUMADJEU TCHOUAGA", "Rodrigue", "08U0045", "M", "SD"),
    ("DASSI MANDJO", "Léa Justine", "22W2164", "F", "SD"),
    ("DAWAI", "Hosse'a", "21T2436", "F", "SD"),
    ("DIBAKTO DEBAMI", "Manich Jordan", "25G2042", "M", "SD"),
    ("DJAMPA MBIANGANG", "Platiny Cabrel", "21T2437", "M", "SD"),
    ("DJATCHE NKAMGANG", "Sylvano", "22W2163", "M", "SD"),
    ("DONGMO TCHOUMENE", "Anita Belviane", "22W2184", "F", "SD"),
    ("ETOUNDI TSANGA", "Elihu Frederic", "22Y567", "M", "SD"),
    ("GOUJOU GUIMATSA", "Zidane", "21T2899", "M", "SD"),
    ("JIATSA DONHACHI", "Rommel Junior", "22T2906", "M", "SD"),
    ("KELODJOU DJOMO", "Nafissatou Ivana", "22T2894", "F", "SD"),
    ("KEMBOU FOSSO", "Richel", "22U2118", "M", "SD"),
    ("KONZOU SODEA", "Alan Perec", "22T2957", "M", "SD"),
    ("KUATE FOKO", "Duford", "20U2953", "M", "SD"),
    ("KUITCHE", "Arolle Nachard", "22T2931", "M", "SD"),
    ("MEFFO TAHAFO", "Léa Jecy", "22U2194", "F", "SD"),
    ("MELONG", "Lethycia", "22W2147", "F", "SD"),
    ("MENGUE ONDOUA", "Claude Kerane", "25G2071", "F", "SD"),
    ("MOUGOU OWOUNDI", "Brice William", "25G2080", "M", "SD"),
    ("NANGMO FEULFACK", "Annick Duplesse", "21S2530", "M", "SD"),
    ("NDEKEBAI MEYIE", "Michael", "21T2707", "M", "SD"),
    ("NDJATIO NGUETSA", "Pechi Lucrece", "18T2796", "F", "SD"),
    ("NGATCHANGUE SIEWE", "Nel", "22U2032", "M", "SD"),
    ("NGONMAN MATCHABO", "Aubert Adrien", "25G2031", "M", "SD"),
    ("NGUEFACK TANGOMO", "Chris Arthur", "25G2055", "M", "SD"),
    ("NZOMUTCHA TAFFOR", "Severin", "19M2157", "M", "SD"),
    ("TAGNE TALLA", "Idriss Chanel", "19M2351", "M", "SD"),
    ("TAPAH NGASSA", "Claudia", "20V2342", "F", "SD"),
    ("TCHANKUIMEU MEUGHELA", "Amaelle", "21T2548", "F", "SD"),
    ("TCHUINTE LINKA", "Martiale", "22T2829", "F", "SD"),
    ("TSAGUE", "Momo", "21T2603", "M", "SD"),
    ("TSEMEGNE", "Martin Yvan", "22U2080", "M", "SD"),
    ("VOUKENG DJIOKENG", "Christian Roussel", "22U2053", "M", "SD"),
]

def add_student(tx, nom, prenom, matricule, sexe, specialite):
    nom_upper = nom.upper()
    prenom_cap = prenom.capitalize()
    date_naissance = "2000-01-01"  # valeur par défaut, à modifier si besoin
    tx.run("""
        MERGE (e:Etudiant {matricule: $matricule})
        SET e.nom = $nom,
            e.prenom = $prenom,
            e.sexe = $sexe,
            e.specialite = $specialite,
            e.date_naissance = $date_naissance
        WITH e
        MATCH (f:Filiere {code: 'INFO'})
        MATCH (n:Niveau {rang: 4, filiere: 'INFO'})
        MERGE (e)-[:INSCRIT_DANS]->(f)
        MERGE (e)-[:EST_EN]->(n)
    """, matricule=matricule, nom=nom_upper, prenom=prenom_cap,
       sexe=sexe, specialite=specialite, date_naissance=date_naissance)

def main():
    with driver.session() as session:
        print("🔄 Ajout des étudiants M1...")
        from collections import Counter
        counts = Counter()
        for nom, prenom, matricule, sexe, specialite in ETUDIANTS:
            session.execute_write(add_student, nom, prenom, matricule, sexe, specialite)
            counts[specialite] += 1
            print(f"   + {nom} {prenom} ({matricule}) - {specialite}")
        print("\n✅ Tous les étudiants ont été ajoutés avec succès !")
        for sp, nb in counts.items():
            print(f"   • {sp}: {nb} étudiants")
    driver.close()

if __name__ == "__main__":
    main()