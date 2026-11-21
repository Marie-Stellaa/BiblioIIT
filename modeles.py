from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass(frozen=True)
class Livre:
    code: str
    titre: str
    auteur: str
    annee: int


@dataclass(frozen=True)
class Etudiant:
    matricule: str
    nom: str


@dataclass
class Pret:
    code_livre: str
    matricule: str
    date_emprunt: date
    date_retour_prevue: date
    date_retour: Optional[date] = None
    id: Optional[int] = None

    @property
    def en_cours(self) -> bool:
        return self.date_retour is None