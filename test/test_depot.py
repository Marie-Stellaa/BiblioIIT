from datetime import date
from modeles import Pret


def test_recherche_par_auteur(depot):
    assert len(depot.chercher_livres("Kourouma")) == 2


def test_cycle_pret(depot):
    pret = depot.enregistrer_pret(
        Pret("L002", "E2026-001", date(2026, 10, 1), date(2026, 10, 15)))
    assert pret.id is not None
    assert depot.pret_en_cours_du_livre("L002") is not None
    assert depot.compter_prets_en_cours("E2026-001") == 1
    depot.cloturer_pret(pret.id, date(2026, 10, 5))
    assert depot.pret_en_cours_du_livre("L002") is None