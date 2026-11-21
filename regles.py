from datetime import date, timedelta

DUREE_PRET_JOURS = 14
MAX_PRETS_PAR_ETUDIANT = 3


def date_retour_prevue(date_emprunt: date) -> date:
    return date_emprunt + timedelta(days=DUREE_PRET_JOURS)


def peut_emprunter(nb_prets_en_cours: int) -> bool:
    return nb_prets_en_cours < MAX_PRETS_PAR_ETUDIANT


def jours_de_retard(date_prevue: date, aujourdhui: date) -> int:
    return max(0, (aujourdhui - date_prevue).days)


def est_en_retard(date_prevue: date, aujourdhui: date) -> bool:
    return jours_de_retard(date_prevue, aujourdhui) > 0