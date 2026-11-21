import sqlite3
from datetime import date
from typing import List, Optional

from modeles import (Document, Exemplaire, Adherent, Pret, Reservation,
                     ATTENTE, PRETE)

SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titre TEXT NOT NULL,
    auteur TEXT NOT NULL,
    annee INTEGER,
    categorie TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS exemplaires (
    code_barres TEXT PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(id),
    statut TEXT NOT NULL DEFAULT 'disponible'
);
CREATE TABLE IF NOT EXISTS adherents (
    matricule TEXT PRIMARY KEY,
    nom TEXT NOT NULL,
    suspendu_jusqu TEXT
);
CREATE TABLE IF NOT EXISTS prets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code_barres TEXT NOT NULL REFERENCES exemplaires(code_barres),
    matricule TEXT NOT NULL REFERENCES adherents(matricule),
    date_emprunt TEXT NOT NULL,
    date_retour_prevue TEXT NOT NULL,
    date_retour TEXT,
    nb_prolongations INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS reservations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL REFERENCES documents(id),
    matricule TEXT NOT NULL REFERENCES adherents(matricule),
    date_reservation TEXT NOT NULL,
    statut TEXT NOT NULL,
    code_barres TEXT
);
"""

COL_PRET = ("id, code_barres, matricule, date_emprunt, date_retour_prevue, "
            "date_retour, nb_prolongations")
COL_RESA = "id, document_id, matricule, date_reservation, statut, code_barres"


def _date(s: Optional[str]) -> Optional[date]:
    return date.fromisoformat(s) if s else None


def _iso(d: Optional[date]) -> Optional[str]:
    return d.isoformat() if d else None


def _pret(l) -> Pret:
    return Pret(id=l[0], code_barres=l[1], matricule=l[2],
                date_emprunt=_date(l[3]), date_retour_prevue=_date(l[4]),
                date_retour=_date(l[5]), nb_prolongations=l[6])


def _resa(l) -> Reservation:
    return Reservation(id=l[0], document_id=l[1], matricule=l[2],
                       date_reservation=_date(l[3]), statut=l[4],
                       code_barres=l[5])


class DepotSqlite:
    """Seul module qui connaît SQL."""

    def __init__(self, chemin: str = "biblioiit.db"):
        self.conn = sqlite3.connect(chemin)
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    # ---------- documents ----------
    def ajouter_document(self, d: Document) -> Document:
        cur = self.conn.execute(
            "INSERT INTO documents (titre, auteur, annee, categorie) "
            "VALUES (?, ?, ?, ?)", (d.titre, d.auteur, d.annee, d.categorie))
        self.conn.commit()
        return Document(cur.lastrowid, d.titre, d.auteur, d.annee, d.categorie)

    def obtenir_document(self, doc_id: int) -> Optional[Document]:
        l = self.conn.execute(
            "SELECT id, titre, auteur, annee, categorie FROM documents "
            "WHERE id = ?", (doc_id,)).fetchone()
        return Document(*l) if l else None

    def chercher_documents(self, mot: str) -> List[Document]:
        m = f"%{mot}%"
        lignes = self.conn.execute(
            "SELECT id, titre, auteur, annee, categorie FROM documents "
            "WHERE titre LIKE ? OR auteur LIKE ? OR categorie LIKE ? "
            "ORDER BY titre", (m, m, m)).fetchall()
        return [Document(*l) for l in lignes]

    def nombre_documents(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]

    # ---------- exemplaires ----------
    def ajouter_exemplaire(self, e: Exemplaire) -> None:
        self.conn.execute(
            "INSERT INTO exemplaires (code_barres, document_id, statut) "
            "VALUES (?, ?, ?)", (e.code_barres, e.document_id, e.statut))
        self.conn.commit()

    def obtenir_exemplaire(self, code: str) -> Optional[Exemplaire]:
        l = self.conn.execute(
            "SELECT code_barres, document_id, statut FROM exemplaires "
            "WHERE code_barres = ?", (code,)).fetchone()
        return Exemplaire(*l) if l else None

    def exemplaires_du_document(self, doc_id: int) -> List[Exemplaire]:
        lignes = self.conn.execute(
            "SELECT code_barres, document_id, statut FROM exemplaires "
            "WHERE document_id = ? ORDER BY code_barres", (doc_id,)).fetchall()
        return [Exemplaire(*l) for l in lignes]

    def changer_statut_exemplaire(self, code: str, statut: str) -> None:
        self.conn.execute("UPDATE exemplaires SET statut = ? "
                          "WHERE code_barres = ?", (statut, code))
        self.conn.commit()

    # ---------- adhérents ----------
    def ajouter_adherent(self, a: Adherent) -> None:
        self.conn.execute(
            "INSERT INTO adherents (matricule, nom, suspendu_jusqu) "
            "VALUES (?, ?, ?)", (a.matricule, a.nom, _iso(a.suspendu_jusqu)))
        self.conn.commit()

    def obtenir_adherent(self, matricule: str) -> Optional[Adherent]:
        l = self.conn.execute(
            "SELECT matricule, nom, suspendu_jusqu FROM adherents "
            "WHERE matricule = ?", (matricule,)).fetchone()
        return Adherent(l[0], l[1], _date(l[2])) if l else None

    def suspendre_adherent(self, matricule: str, jusqu: Optional[date]) -> None:
        self.conn.execute("UPDATE adherents SET suspendu_jusqu = ? "
                          "WHERE matricule = ?", (_iso(jusqu), matricule))
        self.conn.commit()

    # ---------- prêts ----------
    def enregistrer_pret(self, p: Pret) -> Pret:
        cur = self.conn.execute(
            "INSERT INTO prets (code_barres, matricule, date_emprunt, "
            "date_retour_prevue, nb_prolongations) VALUES (?, ?, ?, ?, ?)",
            (p.code_barres, p.matricule, _iso(p.date_emprunt),
             _iso(p.date_retour_prevue), p.nb_prolongations))
        self.conn.commit()
        p.id = cur.lastrowid
        return p

    def pret_en_cours_de_exemplaire(self, code: str) -> Optional[Pret]:
        l = self.conn.execute(
            f"SELECT {COL_PRET} FROM prets "
            "WHERE code_barres = ? AND date_retour IS NULL", (code,)).fetchone()
        return _pret(l) if l else None

    def prets_en_cours_de(self, matricule: str) -> List[Pret]:
        lignes = self.conn.execute(
            f"SELECT {COL_PRET} FROM prets "
            "WHERE matricule = ? AND date_retour IS NULL "
            "ORDER BY date_retour_prevue", (matricule,)).fetchall()
        return [_pret(l) for l in lignes]

    def prets_en_cours(self) -> List[Pret]:
        lignes = self.conn.execute(
            f"SELECT {COL_PRET} FROM prets WHERE date_retour IS NULL "
            "ORDER BY date_retour_prevue").fetchall()
        return [_pret(l) for l in lignes]

    def compter_prets_total(self, matricule: str) -> int:
        return self.conn.execute(
            "SELECT COUNT(*) FROM prets WHERE matricule = ?",
            (matricule,)).fetchone()[0]

    def cloturer_pret(self, pret_id: int, date_retour: date) -> None:
        self.conn.execute("UPDATE prets SET date_retour = ? WHERE id = ?",
                          (_iso(date_retour), pret_id))
        self.conn.commit()

    def prolonger_pret(self, pret_id: int, nouvelle_date: date,
                       nb_prolongations: int) -> None:
        self.conn.execute(
            "UPDATE prets SET date_retour_prevue = ?, nb_prolongations = ? "
            "WHERE id = ?", (_iso(nouvelle_date), nb_prolongations, pret_id))
        self.conn.commit()

    # ---------- réservations ----------
    def ajouter_reservation(self, r: Reservation) -> Reservation:
        cur = self.conn.execute(
            "INSERT INTO reservations (document_id, matricule, "
            "date_reservation, statut, code_barres) VALUES (?, ?, ?, ?, ?)",
            (r.document_id, r.matricule, _iso(r.date_reservation),
             r.statut, r.code_barres))
        self.conn.commit()
        r.id = cur.lastrowid
        return r

    def file_attente(self, doc_id: int) -> List[Reservation]:
        """Réservations en attente, la plus ancienne en premier."""
        lignes = self.conn.execute(
            f"SELECT {COL_RESA} FROM reservations "
            "WHERE document_id = ? AND statut = ? ORDER BY id",
            (doc_id, ATTENTE)).fetchall()
        return [_resa(l) for l in lignes]

    def reservation_prete(self, doc_id: int, matricule: str) -> Optional[Reservation]:
        l = self.conn.execute(
            f"SELECT {COL_RESA} FROM reservations "
            "WHERE document_id = ? AND matricule = ? AND statut = ?",
            (doc_id, matricule, PRETE)).fetchone()
        return _resa(l) if l else None

    def reservation_active(self, doc_id: int, matricule: str) -> Optional[Reservation]:
        l = self.conn.execute(
            f"SELECT {COL_RESA} FROM reservations "
            "WHERE document_id = ? AND matricule = ? AND statut IN (?, ?)",
            (doc_id, matricule, ATTENTE, PRETE)).fetchone()
        return _resa(l) if l else None

    def reservations_actives_de(self, matricule: str) -> List[Reservation]:
        lignes = self.conn.execute(
            f"SELECT {COL_RESA} FROM reservations "
            "WHERE matricule = ? AND statut IN (?, ?) ORDER BY id",
            (matricule, ATTENTE, PRETE)).fetchall()
        return [_resa(l) for l in lignes]

    def mettre_a_jour_reservation(self, resa_id: int, statut: str,
                                  code_barres: Optional[str] = None) -> None:
        self.conn.execute(
            "UPDATE reservations SET statut = ?, code_barres = ? WHERE id = ?",
            (statut, code_barres, resa_id))
        self.conn.commit()