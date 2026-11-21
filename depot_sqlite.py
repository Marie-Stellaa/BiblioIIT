import sqlite3
from datetime import date
from typing import List, Optional

from modeles import Livre, Etudiant, Pret

SCHEMA = """
CREATE TABLE IF NOT EXISTS livres (
    code TEXT PRIMARY KEY,
    titre TEXT NOT NULL,
    auteur TEXT NOT NULL,
    annee INTEGER
);
CREATE TABLE IF NOT EXISTS etudiants (
    matricule TEXT PRIMARY KEY,
    nom TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS prets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code_livre TEXT NOT NULL REFERENCES livres(code),
    matricule TEXT NOT NULL REFERENCES etudiants(matricule),
    date_emprunt TEXT NOT NULL,
    date_retour_prevue TEXT NOT NULL,
    date_retour TEXT
);
"""

COLONNES_PRET = ("id, code_livre, matricule, date_emprunt, "
                 "date_retour_prevue, date_retour")


def _vers_pret(l) -> Pret:
    return Pret(id=l[0], code_livre=l[1], matricule=l[2],
                date_emprunt=date.fromisoformat(l[3]),
                date_retour_prevue=date.fromisoformat(l[4]),
                date_retour=date.fromisoformat(l[5]) if l[5] else None)


class DepotSqlite:
    def __init__(self, chemin: str = "biblioiit.db"):
        self.conn = sqlite3.connect(chemin)
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    # ---- livres ----
    def ajouter_livre(self, livre: Livre) -> None:
        self.conn.execute("INSERT OR REPLACE INTO livres VALUES (?, ?, ?, ?)",
                          (livre.code, livre.titre, livre.auteur, livre.annee))
        self.conn.commit()

    def obtenir_livre(self, code: str) -> Optional[Livre]:
        l = self.conn.execute(
            "SELECT code, titre, auteur, annee FROM livres WHERE code = ?",
            (code,)).fetchone()
        return Livre(*l) if l else None

    def chercher_livres(self, mot: str) -> List[Livre]:
        motif = f"%{mot}%"
        lignes = self.conn.execute(
            "SELECT code, titre, auteur, annee FROM livres "
            "WHERE titre LIKE ? OR auteur LIKE ? ORDER BY code",
            (motif, motif)).fetchall()
        return [Livre(*l) for l in lignes]

    # ---- étudiants ----
    def ajouter_etudiant(self, etudiant: Etudiant) -> None:
        self.conn.execute("INSERT OR REPLACE INTO etudiants VALUES (?, ?)",
                          (etudiant.matricule, etudiant.nom))
        self.conn.commit()

    def obtenir_etudiant(self, matricule: str) -> Optional[Etudiant]:
        l = self.conn.execute(
            "SELECT matricule, nom FROM etudiants WHERE matricule = ?",
            (matricule,)).fetchone()
        return Etudiant(*l) if l else None

    # ---- prêts ----
    def enregistrer_pret(self, pret: Pret) -> Pret:
        cur = self.conn.execute(
            "INSERT INTO prets (code_livre, matricule, date_emprunt, "
            "date_retour_prevue) VALUES (?, ?, ?, ?)",
            (pret.code_livre, pret.matricule, pret.date_emprunt.isoformat(),
             pret.date_retour_prevue.isoformat()))
        self.conn.commit()
        pret.id = cur.lastrowid
        return pret

    def pret_en_cours_du_livre(self, code: str) -> Optional[Pret]:
        l = self.conn.execute(
            f"SELECT {COLONNES_PRET} FROM prets "
            "WHERE code_livre = ? AND date_retour IS NULL", (code,)).fetchone()
        return _vers_pret(l) if l else None

    def compter_prets_en_cours(self, matricule: str) -> int:
        return self.conn.execute(
            "SELECT COUNT(*) FROM prets "
            "WHERE matricule = ? AND date_retour IS NULL",
            (matricule,)).fetchone()[0]

    def cloturer_pret(self, pret_id: int, date_retour: date) -> None:
        self.conn.execute("UPDATE prets SET date_retour = ? WHERE id = ?",
                          (date_retour.isoformat(), pret_id))
        self.conn.commit()

    def prets_en_cours(self) -> List[Pret]:
        lignes = self.conn.execute(
            f"SELECT {COLONNES_PRET} FROM prets WHERE date_retour IS NULL "
            "ORDER BY date_retour_prevue").fetchall()
        return [_vers_pret(l) for l in lignes]