from dataclasses import dataclass
from datetime import date, timedelta
from typing import Callable, List, Optional, Tuple

import regles
from modeles import (Document, Exemplaire, Adherent, Pret, Reservation,
                     DISPONIBLE, EMPRUNTE, RESERVE, PERDU, REPARATION,
                     ATTENTE, PRETE, TERMINEE)


class ErreurBiblio(Exception):
    """Erreur métier, affichable telle quelle à l'utilisateur."""


@dataclass
class ResultatRecherche:
    document: Document
    total: int          # exemplaires hors perdus
    disponibles: int
    en_attente: int     # réservations en file


@dataclass
class ResultatRetour:
    pret: Pret
    document: Document
    jours_retard: int
    suspendu_jusqu: Optional[date]
    reservation_servie: Optional[Reservation]


@dataclass
class FicheAdherent:
    adherent: Adherent
    prets: List[Tuple[Pret, Document, int]]          # (prêt, document, retard)
    reservations: List[Tuple[Reservation, Document]]
    total_prets: int
    suspendu: bool


class ServiceBibliotheque:
    def __init__(self, depot, aujourdhui: Callable[[], date] = date.today):
        self.depot = depot
        self.aujourdhui = aujourdhui

    # ---------- outils internes ----------
    def _exemplaire(self, code: str) -> Exemplaire:
        ex = self.depot.obtenir_exemplaire(code)
        if ex is None:
            raise ErreurBiblio(f"Exemplaire inconnu : {code}.")
        return ex

    def _document(self, doc_id: int) -> Document:
        doc = self.depot.obtenir_document(doc_id)
        if doc is None:
            raise ErreurBiblio("Document inconnu.")
        return doc

    def _liberer(self, code: str, doc_id: int) -> Optional[Reservation]:
        """Un exemplaire redevient libre : on le met de côté pour le 1er de la
        file d'attente, sinon il redevient disponible."""
        file = self.depot.file_attente(doc_id)
        if file:
            r = file[0]
            self.depot.mettre_a_jour_reservation(r.id, PRETE, code)
            self.depot.changer_statut_exemplaire(code, RESERVE)
            r.statut, r.code_barres = PRETE, code
            return r
        self.depot.changer_statut_exemplaire(code, DISPONIBLE)
        return None

    # ---------- consultation ----------
    def identifier(self, matricule: str) -> Adherent:
        a = self.depot.obtenir_adherent(matricule)
        if a is None:
            raise ErreurBiblio(f"Adhérent inconnu : {matricule}.")
        return a

    def rechercher(self, mot: str) -> List[ResultatRecherche]:
        resultats = []
        for d in self.depot.chercher_documents(mot.strip()):
            exs = [e for e in self.depot.exemplaires_du_document(d.id)
                   if e.statut != PERDU]
            dispo = sum(1 for e in exs if e.statut == DISPONIBLE)
            attente = len(self.depot.file_attente(d.id))
            resultats.append(ResultatRecherche(d, len(exs), dispo, attente))
        return resultats

    def prets_en_cours(self) -> List[Tuple[Pret, Document]]:
        return [(p, self._document(self._exemplaire(p.code_barres).document_id))
                for p in self.depot.prets_en_cours()]

    def retards(self) -> List[Tuple[Pret, Document, int]]:
        auj = self.aujourdhui()
        return [(p, d, regles.jours_de_retard(p.date_retour_prevue, auj))
                for p, d in self.prets_en_cours()
                if regles.est_en_retard(p.date_retour_prevue, auj)]

    def fiche(self, matricule: str) -> FicheAdherent:
        a = self.identifier(matricule)
        auj = self.aujourdhui()
        prets = []
        for p in self.depot.prets_en_cours_de(matricule):
            doc = self._document(self._exemplaire(p.code_barres).document_id)
            prets.append((p, doc, regles.jours_de_retard(p.date_retour_prevue, auj)))
        resas = [(r, self._document(r.document_id))
                 for r in self.depot.reservations_actives_de(matricule)]
        return FicheAdherent(a, prets, resas,
                             self.depot.compter_prets_total(matricule),
                             regles.est_suspendu(a.suspendu_jusqu, auj))

    # ---------- emprunt ----------
    def emprunter(self, code: str, matricule: str) -> Pret:
        ex = self._exemplaire(code)
        adherent = self.identifier(matricule)
        doc = self._document(ex.document_id)
        auj = self.aujourdhui()

        if ex.statut == EMPRUNTE:
            raise ErreurBiblio(f"L'exemplaire {code} est déjà emprunté.")
        if ex.statut in (PERDU, REPARATION):
            raise ErreurBiblio(
                f"L'exemplaire {code} n'est pas empruntable (état : {ex.statut}).")
        if regles.est_suspendu(adherent.suspendu_jusqu, auj):
            raise ErreurBiblio(
                f"{adherent.nom} est suspendu jusqu'au "
                f"{adherent.suspendu_jusqu.strftime('%d/%m/%Y')}.")
        en_cours = self.depot.prets_en_cours_de(matricule)
        if any(regles.est_en_retard(p.date_retour_prevue, auj) for p in en_cours):
            raise ErreurBiblio(f"{adherent.nom} a un prêt en retard à rendre d'abord.")
        if not regles.peut_emprunter(len(en_cours)):
            raise ErreurBiblio(
                f"{adherent.nom} a atteint la limite de "
                f"{regles.MAX_PRETS_PAR_ADHERENT} prêts.")

        resa = self.depot.reservation_prete(doc.id, matricule)
        if ex.statut == RESERVE and (resa is None or resa.code_barres != code):
            raise ErreurBiblio(
                f"L'exemplaire {code} est réservé pour un autre adhérent.")
        if resa:
            self.depot.mettre_a_jour_reservation(resa.id, TERMINEE, resa.code_barres)
            if resa.code_barres != code:        # il prend un autre exemplaire
                self._liberer(resa.code_barres, doc.id)

        pret = self.depot.enregistrer_pret(
            Pret(code, matricule, auj, regles.date_retour_prevue(auj)))
        self.depot.changer_statut_exemplaire(code, EMPRUNTE)
        return pret

    def emprunter_document(self, doc_id: int, matricule: str) -> Pret:
        """Choisit automatiquement l'exemplaire à prêter."""
        self._document(doc_id)
        resa = self.depot.reservation_prete(doc_id, matricule)
        if resa:
            return self.emprunter(resa.code_barres, matricule)
        for ex in self.depot.exemplaires_du_document(doc_id):
            if ex.statut == DISPONIBLE:
                return self.emprunter(ex.code_barres, matricule)
        raise ErreurBiblio("Aucun exemplaire disponible. Vous pouvez le réserver.")

    # ---------- retour ----------
    def rendre(self, code: str) -> ResultatRetour:
        ex = self._exemplaire(code)
        if ex.statut != EMPRUNTE:
            raise ErreurBiblio(f"L'exemplaire {code} n'est pas emprunté.")
        pret = self.depot.pret_en_cours_de_exemplaire(code)
        doc = self._document(ex.document_id)
        auj = self.aujourdhui()
        self.depot.cloturer_pret(pret.id, auj)

        jours = regles.jours_de_retard(pret.date_retour_prevue, auj)
        jusqu = None
        if jours:
            jusqu = auj + timedelta(days=regles.duree_suspension(jours))
            actuel = self.depot.obtenir_adherent(pret.matricule).suspendu_jusqu
            if actuel and actuel > jusqu:
                jusqu = actuel
            self.depot.suspendre_adherent(pret.matricule, jusqu)

        servie = self._liberer(code, doc.id)
        return ResultatRetour(pret, doc, jours, jusqu, servie)

    # ---------- prolongation ----------
    def prolonger(self, code: str) -> Pret:
        ex = self._exemplaire(code)
        pret = self.depot.pret_en_cours_de_exemplaire(code)
        if pret is None:
            raise ErreurBiblio(f"L'exemplaire {code} n'est pas emprunté.")
        if regles.est_en_retard(pret.date_retour_prevue, self.aujourdhui()):
            raise ErreurBiblio("Prolongation impossible : le prêt est en retard.")
        if not regles.peut_prolonger(pret.nb_prolongations):
            raise ErreurBiblio(
                f"Prolongation impossible : limite de "
                f"{regles.MAX_PROLONGATIONS} prolongation(s) atteinte.")
        if self.depot.file_attente(ex.document_id):
            raise ErreurBiblio("Prolongation impossible : document réservé "
                               "par un autre adhérent.")
        nouvelle = regles.date_apres_prolongation(pret.date_retour_prevue)
        self.depot.prolonger_pret(pret.id, nouvelle, pret.nb_prolongations + 1)
        pret.date_retour_prevue = nouvelle
        pret.nb_prolongations += 1
        return pret

    # ---------- réservation ----------
    def reserver(self, doc_id: int, matricule: str) -> Tuple[Reservation, int]:
        """Retourne (réservation, position dans la file)."""
        doc = self._document(doc_id)
        self.identifier(matricule)
        exs = [e for e in self.depot.exemplaires_du_document(doc_id)
               if e.statut != PERDU]
        if not exs:
            raise ErreurBiblio("Aucun exemplaire en circulation pour ce document.")
        if any(e.statut == DISPONIBLE for e in exs):
            raise ErreurBiblio("Un exemplaire est disponible : empruntez-le directement.")
        if self.depot.reservation_active(doc_id, matricule):
            raise ErreurBiblio("Vous avez déjà réservé ce document.")
        for p in self.depot.prets_en_cours_de(matricule):
            if self._exemplaire(p.code_barres).document_id == doc_id:
                raise ErreurBiblio("Vous avez déjà ce document en prêt.")
        r = self.depot.ajouter_reservation(
            Reservation(doc.id, matricule, self.aujourdhui()))
        return r, len(self.depot.file_attente(doc_id))

    # ---------- gestion du catalogue ----------
    def inscrire_adherent(self, matricule: str, nom: str) -> Adherent:
        matricule, nom = matricule.strip().upper(), nom.strip()
        if not matricule or not nom:
            raise ErreurBiblio("Matricule et nom obligatoires.")
        if self.depot.obtenir_adherent(matricule):
            raise ErreurBiblio(f"Le matricule {matricule} existe déjà.")
        a = Adherent(matricule, nom)
        self.depot.ajouter_adherent(a)
        return a

    def ajouter_document(self, titre: str, auteur: str, annee: int,
                         categorie: str, nb_exemplaires: int = 1) -> Document:
        if not (titre.strip() and auteur.strip() and categorie.strip()):
            raise ErreurBiblio("Titre, auteur et catégorie obligatoires.")
        if nb_exemplaires < 1:
            raise ErreurBiblio("Il faut au moins un exemplaire.")
        doc = self.depot.ajouter_document(
            Document(None, titre.strip(), auteur.strip(), annee, categorie.strip()))
        for _ in range(nb_exemplaires):
            self.ajouter_exemplaire(doc.id)
        return doc

    def ajouter_exemplaire(self, doc_id: int) -> Exemplaire:
        self._document(doc_id)
        numero = len(self.depot.exemplaires_du_document(doc_id)) + 1
        ex = Exemplaire(f"D{doc_id:03d}-{numero:02d}", doc_id)
        self.depot.ajouter_exemplaire(ex)
        self._liberer(ex.code_barres, doc_id)     
        return self._exemplaire(ex.code_barres)

    def changer_etat(self, code: str, statut: str) -> Exemplaire:
        ex = self._exemplaire(code)
        if statut not in (DISPONIBLE, PERDU, REPARATION):
            raise ErreurBiblio("État non autorisé.")
        if ex.statut in (EMPRUNTE, RESERVE):
            raise ErreurBiblio(f"Impossible : l'exemplaire est {ex.statut}.")
        if statut == DISPONIBLE:
            self._liberer(code, ex.document_id)
        else:
            self.depot.changer_statut_exemplaire(code, statut)
        return self._exemplaire(code)