from datetime import date
from typing import Callable, List, Tuple

import regles
from modeles import Livre, Pret


class ErreurBiblio(Exception):
    """Erreur métier, affichable telle quelle à l'utilisateur."""


class ServiceBibliotheque:
    def __init__(self, depot, aujourdhui: Callable[[], date] = date.today):
        self.depot = depot
        self.aujourdhui = aujourdhui

    def rechercher(self, mot: str) -> List[Tuple[Livre, bool]]:
        """Retourne (livre, est_disponible) pour chaque résultat."""
        return [(l, self.depot.pret_en_cours_du_livre(l.code) is None)
                for l in self.depot.chercher_livres(mot.strip())]

    def emprunter(self, code: str, matricule: str) -> Pret:
        livre = self.depot.obtenir_livre(code)
        if livre is None:
            raise ErreurBiblio(f"Livre inconnu : {code}.")
        if self.depot.obtenir_etudiant(matricule) is None:
            raise ErreurBiblio(f"Étudiant inconnu : {matricule}.")
        if self.depot.pret_en_cours_du_livre(code):
            raise ErreurBiblio(f"Le livre « {livre.titre} » est déjà emprunté.")
        if not regles.peut_emprunter(self.depot.compter_prets_en_cours(matricule)):
            raise ErreurBiblio(
                f"{matricule} a atteint la limite de "
                f"{regles.MAX_PRETS_PAR_ETUDIANT} prêts.")
        debut = self.aujourdhui()
        pret = Pret(code_livre=code, matricule=matricule, date_emprunt=debut,
                    date_retour_prevue=regles.date_retour_prevue(debut))
        return self.depot.enregistrer_pret(pret)

    def rendre(self, code: str) -> Pret:
        livre = self.depot.obtenir_livre(code)
        if livre is None:
            raise ErreurBiblio(f"Livre inconnu : {code}.")
        pret = self.depot.pret_en_cours_du_livre(code)
        if pret is None:
            raise ErreurBiblio(f"Le livre « {livre.titre} » n'est pas emprunté.")
        self.depot.cloturer_pret(pret.id, self.aujourdhui())
        return pret

    def retards(self) -> List[Tuple[Pret, Livre, int]]:
        """Retourne (prêt, livre, jours de retard) pour les prêts en retard."""
        auj = self.aujourdhui()
        resultat = []
        for p in self.depot.prets_en_cours():
            if regles.est_en_retard(p.date_retour_prevue, auj):
                resultat.append((p, self.depot.obtenir_livre(p.code_livre),
                                 regles.jours_de_retard(p.date_retour_prevue, auj)))
        return resultat