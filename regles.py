from datetime import date, timedelta
from typing import Optional

DUREE_PRET_JOURS = 14
MAX_PRETS_PAR_ADHERENT = 3
MAX_PROLONGATIONS = 1
DUREE_PROLONGATION_JOURS = 7
JOURS_SUSPENSION_PAR_JOUR_DE_RETARD = 2


def date_retour_prevue(date_emprunt: date) -> date:
    return date_emprunt + timedelta(days=DUREE_PRET_JOURS)


def peut_emprunter(nb_prets_en_cours: int) -> bool:
    return nb_prets_en_cours < MAX_PRETS_PAR_ADHERENT


def jours_de_retard(date_prevue: date, aujourdhui: date) -> int:
    return max(0, (aujourdhui - date_prevue).days)


def est_en_retard(date_prevue: date, aujourdhui: date) -> bool:
    return jours_de_retard(date_prevue, aujourdhui) > 0


def duree_suspension(jours_retard: int) -> int:
    """Nombre de jours sans pouvoir emprunter, proportionnel au retard."""
    return jours_retard * JOURS_SUSPENSION_PAR_JOUR_DE_RETARD


def est_suspendu(suspendu_jusqu: Optional[date], aujourdhui: date) -> bool:
    return suspendu_jusqu is not None and aujourdhui < suspendu_jusqu


def peut_prolonger(nb_prolongations: int) -> bool:
    return nb_prolongations < MAX_PROLONGATIONS


def date_apres_prolongation(date_prevue: date) -> date:
    return date_prevue + timedelta(days=DUREE_PROLONGATION_JOURS)