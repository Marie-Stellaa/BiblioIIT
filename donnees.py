from datetime import date, timedelta

import regles
from modeles import (Document, Exemplaire, Adherent, Pret, Reservation,
                     EMPRUNTE)

# (titre, auteur, année, catégorie, nombre d'exemplaires)
# Le document n°i reçoit les codes-barres D{i:03d}-01, -02, ...
CATALOGUE = [
    ("En attendant le vote des bêtes sauvages", "Ahmadou Kourouma", 1998, "Roman africain", 2),
    ("Les Soleils des indépendances", "Ahmadou Kourouma", 1968, "Roman africain", 3),
    ("Monnè, outrages et défis", "Ahmadou Kourouma", 1990, "Roman africain", 1),
    ("Allah n'est pas obligé", "Ahmadou Kourouma", 2000, "Roman africain", 2),
    ("Climbié", "Bernard Dadié", 1956, "Roman africain", 2),
    ("Un nègre à Paris", "Bernard Dadié", 1959, "Roman africain", 1),
    ("Le Pagne noir", "Bernard Dadié", 1955, "Conte", 1),
    ("Une si longue lettre", "Mariama Bâ", 1979, "Roman africain", 3),
    ("L'Aventure ambiguë", "Cheikh Hamidou Kane", 1961, "Roman africain", 1),
    ("Le monde s'effondre", "Chinua Achebe", 1958, "Roman africain", 2),
    ("L'Enfant noir", "Camara Laye", 1953, "Roman africain", 2),
    ("Les Bouts de bois de Dieu", "Ousmane Sembène", 1960, "Roman africain", 1),
    ("Amkoullel, l'enfant peul", "Amadou Hampâté Bâ", 1991, "Autobiographie", 1),
    ("Cahier d'un retour au pays natal", "Aimé Césaire", 1939, "Poésie", 1),
    ("La Vie et demie", "Sony Labou Tansi", 1979, "Roman africain", 1),
    ("Reine Pokou", "Véronique Tadjo", 2004, "Roman africain", 1),
    ("Le Ventre de l'Atlantique", "Fatou Diome", 2003, "Roman africain", 1),
    ("Les Misérables", "Victor Hugo", 1862, "Classique", 3),
    ("Notre-Dame de Paris", "Victor Hugo", 1831, "Classique", 2),
    ("Le Petit Prince", "Antoine de Saint-Exupéry", 1943, "Classique", 3),
    ("L'Étranger", "Albert Camus", 1942, "Classique", 2),
    ("La Peste", "Albert Camus", 1947, "Classique", 2),
    ("Germinal", "Émile Zola", 1885, "Classique", 2),
    ("Candide", "Voltaire", 1759, "Classique", 1),
    ("Le Père Goriot", "Honoré de Balzac", 1835, "Classique", 1),
    ("Madame Bovary", "Gustave Flaubert", 1857, "Classique", 1),
    ("Le Rouge et le Noir", "Stendhal", 1830, "Classique", 1),
    ("L'Alchimiste", "Paulo Coelho", 1988, "Roman", 2),
    ("Sapiens", "Yuval Noah Harari", 2011, "Essai", 2),
    ("Père riche, père pauvre", "Robert Kiyosaki", 1997, "Essai", 2),
    ("Apprendre à programmer avec Python 3", "Gérard Swinnen", 2012, "Informatique", 3),
    ("Clean Code", "Robert C. Martin", 2008, "Informatique", 2),
    ("The Pragmatic Programmer", "Andrew Hunt et David Thomas", 1999, "Informatique", 1),
    ("Design Patterns", "Erich Gamma et al.", 1994, "Informatique", 1),
    ("Introduction to Algorithms", "Thomas Cormen et al.", 2009, "Informatique", 2),
    ("Réseaux", "Andrew Tanenbaum", 2010, "Informatique", 1),
]

ADHERENTS = [
    ("E2026-001", "Awa Koné"), ("E2026-002", "Yao Kouassi"),
    ("E2026-003", "Fatoumata Traoré"), ("E2026-004", "Koffi N'Guessan"),
    ("E2026-005", "Aminata Diallo"), ("E2026-006", "Jean-Marc Bamba"),
    ("E2026-007", "Adjoua Kouamé"), ("E2026-008", "Ibrahim Ouattara"),
    ("E2026-009", "Marie-Laure Aka"), ("E2026-010", "Serge Yapi"),
]

# (code-barres, matricule, emprunté il y a N jours)
PRETS_EN_COURS = [
    ("D002-01", "E2026-001", 20),  
    ("D032-01", "E2026-002", 16),   
    ("D034-01", "E2026-003", 5),    
    ("D021-01", "E2026-004", 3),
]


def charger_donnees(depot):
    """Remplit la base avec un catalogue réaliste (première exécution)."""
    for titre, auteur, annee, categorie, nb in CATALOGUE:
        doc = depot.ajouter_document(Document(None, titre, auteur, annee, categorie))
        for n in range(1, nb + 1):
            depot.ajouter_exemplaire(Exemplaire(f"D{doc.id:03d}-{n:02d}", doc.id))
    for matricule, nom in ADHERENTS:
        depot.ajouter_adherent(Adherent(matricule, nom))
    for code, matricule, il_y_a in PRETS_EN_COURS:
        debut = date.today() - timedelta(days=il_y_a)
        depot.enregistrer_pret(Pret(code, matricule, debut,
                                    regles.date_retour_prevue(debut)))
        depot.changer_statut_exemplaire(code, EMPRUNTE)
    depot.ajouter_reservation(Reservation(34, "E2026-005", date.today()))