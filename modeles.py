from dataclasses import dataclass
from datetime import date
from typing import Optional

# Statuts d'un exemplaire
DISPONIBLE = "disponible"
EMPRUNTE = "emprunte"
RESERVE = "reserve"          
PERDU = "perdu"
REPARATION = "reparation"

# Statuts d'une réservation
ATTENTE = "attente"
PRETE = "prete"            
TERMINEE = "terminee"


@dataclass(frozen=True)
class Document:
    id: Optional[int]
    titre: str
    auteur: str
    annee: int
    categorie: str


@dataclass
class Exemplaire:
    code_barres: str
    document_id: int
    statut: str = DISPONIBLE


@dataclass
class Adherent:
    matricule: str
    nom: str
    suspendu_jusqu: Optional[date] = None


@dataclass
class Pret:
    code_barres: str
    matricule: str
    date_emprunt: date
    date_retour_prevue: date
    date_retour: Optional[date] = None
    nb_prolongations: int = 0
    id: Optional[int] = None

    @property
    def en_cours(self) -> bool:
        return self.date_retour is None


@dataclass
class Reservation:
    document_id: int
    matricule: str
    date_reservation: date
    statut: str = ATTENTE
    code_barres: Optional[str] = None
    id: Optional[int] = None