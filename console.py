from modeles import DISPONIBLE, PERDU, REPARATION
from service import ErreurBiblio

MENU = """
=== BiblioIIT ===
1. Rechercher un document    5. Réserver
2. Emprunter                 6. Retards
3. Rendre                    7. Fiche d'un adhérent
4. Prolonger                 8. Gestion du catalogue
                             0. Quitter"""

MENU_GESTION = """
--- Gestion du catalogue ---
1. Ajouter un document       3. Changer l'état d'un exemplaire
2. Ajouter un exemplaire     4. Inscrire un adhérent
0. Retour"""


def fmt(d):
    return d.strftime("%d/%m/%Y")


class Console:
    def __init__(self, service, entree=input, sortie=print):
        self.service = service
        self.entree = entree
        self.sortie = sortie

    # ---------- boucle principale ----------
    def lancer(self):
        actions = {"1": self.rechercher, "2": self.emprunter,
                   "3": self.rendre, "4": self.prolonger,
                   "5": self.reserver, "6": self.retards,
                   "7": self.fiche, "8": self.gestion}
        while True:
            self.sortie(MENU)
            choix = self.entree("Votre choix : ").strip()
            if choix == "0":
                self.sortie("Au revoir !")
                return
            action = actions.get(choix)
            if action is None:
                self.sortie("Choix invalide.")
                continue
            self._executer(action)

    def _executer(self, action):
        try:
            action()
        except ErreurBiblio as e:
            self.sortie(f"Impossible : {e}")
        except ValueError:
            self.sortie("Impossible : saisie numérique invalide.")

    # ---------- outils ----------
    def _ligne_resultat(self, r):
        d = r.document
        ligne = (f"D{d.id:03d}  {d.titre} - {d.auteur} ({d.annee}) "
                 f"[{d.categorie}]  {r.disponibles}/{r.total} dispo")
        if r.en_attente:
            ligne += f", {r.en_attente} réservation(s)"
        return ligne

    def _choisir(self, options, texte):
        """Liste numérotée de (objet, texte). Retourne l'objet ou None."""
        for i, (_, ligne) in enumerate(options, start=1):
            self.sortie(f"  {i:>2}. {ligne}")
        rep = self.entree(f"{texte} (Entrée pour annuler) : ").strip()
        if not rep:
            return None
        if rep.isdigit() and 1 <= int(rep) <= len(options):
            return options[int(rep) - 1][0]
        self.sortie("Numéro invalide.")
        return None

    def _chercher_document(self):
        mot = self.entree("Recherche (titre, auteur ou catégorie) : ")
        resultats = self.service.rechercher(mot)
        if not resultats:
            self.sortie("Aucun résultat.")
            return None
        options = [(r.document, self._ligne_resultat(r)) for r in resultats]
        return self._choisir(options, "Numéro du document")

    def _adherent(self):
        matricule = self.entree("Matricule de l'adhérent : ").strip().upper()
        return self.service.identifier(matricule)

    # ---------- actions ----------
    def rechercher(self):
        mot = self.entree("Recherche (titre, auteur ou catégorie, vide = tout) : ")
        resultats = self.service.rechercher(mot)
        if not resultats:
            self.sortie("Aucun résultat.")
        for r in resultats:
            self.sortie("  " + self._ligne_resultat(r))

    def emprunter(self):
        a = self._adherent()
        self.sortie(f"Bonjour {a.nom}.")
        doc = self._chercher_document()
        if doc is None:
            return
        pret = self.service.emprunter_document(doc.id, a.matricule)
        self.sortie(f"Emprunt enregistré : « {doc.titre} » "
                    f"(exemplaire {pret.code_barres}). "
                    f"Retour prévu le {fmt(pret.date_retour_prevue)}.")

    def rendre(self):
        code = self.entree("Code-barres de l'exemplaire "
                           "(Entrée pour choisir dans la liste) : ").strip().upper()
        if not code:
            prets = self.service.prets_en_cours()
            if not prets:
                self.sortie("Aucun prêt en cours.")
                return
            options = [(p.code_barres,
                        f"{p.code_barres}  {d.titre} - {p.matricule} "
                        f"(à rendre le {fmt(p.date_retour_prevue)})")
                       for p, d in prets]
            code = self._choisir(options, "Numéro du prêt à clôturer")
            if code is None:
                return
        r = self.service.rendre(code)
        self.sortie(f"« {r.document.titre} » rendu. Merci !")
        if r.jours_retard:
            self.sortie(f"  Retard de {r.jours_retard} jour(s) : emprunts "
                        f"suspendus jusqu'au {fmt(r.suspendu_jusqu)}.")
        if r.reservation_servie:
            self.sortie(f"  Exemplaire mis de côté pour "
                        f"{r.reservation_servie.matricule} (réservation).")

    def prolonger(self):
        a = self._adherent()
        fiche = self.service.fiche(a.matricule)
        if not fiche.prets:
            self.sortie(f"{a.nom} n'a aucun prêt en cours.")
            return
        options = [(p.code_barres,
                    f"{d.titre} (à rendre le {fmt(p.date_retour_prevue)})")
                   for p, d, _ in fiche.prets]
        code = self._choisir(options, "Numéro du prêt à prolonger")
        if code is None:
            return
        pret = self.service.prolonger(code)
        self.sortie(f"Prêt prolongé. Nouveau retour le "
                    f"{fmt(pret.date_retour_prevue)}.")

    def reserver(self):
        a = self._adherent()
        doc = self._chercher_document()
        if doc is None:
            return
        _, position = self.service.reserver(doc.id, a.matricule)
        self.sortie(f"Réservation enregistrée : « {doc.titre} ». "
                    f"Vous êtes n°{position} dans la file.")

    def retards(self):
        retards = self.service.retards()
        if not retards:
            self.sortie("Aucun retard.")
        for pret, doc, jours in retards:
            self.sortie(f"  {pret.code_barres}  {doc.titre} - {pret.matricule} : "
                        f"{jours} jour(s) de retard "
                        f"(prévu le {fmt(pret.date_retour_prevue)})")

    def fiche(self):
        a = self._adherent()
        f = self.service.fiche(a.matricule)
        self.sortie(f"{a.nom} ({a.matricule}) - {f.total_prets} prêt(s) au total")
        if f.suspendu:
            self.sortie(f"  SUSPENDU jusqu'au {fmt(a.suspendu_jusqu)}")
        self.sortie("Prêts en cours :" if f.prets else "Aucun prêt en cours.")
        for p, d, jours in f.prets:
            retard = f"  EN RETARD de {jours} j" if jours else ""
            self.sortie(f"  {p.code_barres}  {d.titre} - à rendre le "
                        f"{fmt(p.date_retour_prevue)}{retard}")
        for r, d in f.reservations:
            etat = ("à retirer au comptoir" if r.statut == "prete"
                    else "en attente")
            self.sortie(f"  Réservation : {d.titre} ({etat})")

    # ---------- gestion du catalogue ----------
    def gestion(self):
        while True:
            self.sortie(MENU_GESTION)
            choix = self.entree("Votre choix : ").strip()
            if choix == "0":
                return
            actions = {"1": self._ajouter_document, "2": self._ajouter_exemplaire,
                       "3": self._changer_etat, "4": self._inscrire}
            action = actions.get(choix)
            if action is None:
                self.sortie("Choix invalide.")
                continue
            self._executer(action)

    def _ajouter_document(self):
        titre = self.entree("Titre : ")
        auteur = self.entree("Auteur : ")
        annee = int(self.entree("Année : "))
        categorie = self.entree("Catégorie : ")
        nb = int(self.entree("Nombre d'exemplaires : "))
        doc = self.service.ajouter_document(titre, auteur, annee, categorie, nb)
        self.sortie(f"Document ajouté : D{doc.id:03d} ({nb} exemplaire(s)).")

    def _ajouter_exemplaire(self):
        doc = self._chercher_document()
        if doc is None:
            return
        ex = self.service.ajouter_exemplaire(doc.id)
        self.sortie(f"Exemplaire ajouté : {ex.code_barres}.")

    def _changer_etat(self):
        code = self.entree("Code-barres de l'exemplaire : ").strip().upper()
        etats = [(DISPONIBLE, "Disponible (remis en rayon)"),
                 (PERDU, "Perdu"), (REPARATION, "En réparation")]
        statut = self._choisir(etats, "Nouvel état")
        if statut is None:
            return
        ex = self.service.changer_etat(code, statut)
        self.sortie(f"{ex.code_barres} : état « {ex.statut} ».")

    def _inscrire(self):
        matricule = self.entree("Matricule : ")
        nom = self.entree("Nom complet : ")
        a = self.service.inscrire_adherent(matricule, nom)
        self.sortie(f"Adhérent inscrit : {a.nom} ({a.matricule}).")