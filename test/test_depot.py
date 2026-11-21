from datetime import date
from modeles import Pret, Reservation


def test_recherche_par_auteur(depot):
    assert [d.titre for d in depot.chercher_documents("hugo")] == ["Les Misérables"]


def test_exemplaires_du_document(depot):
    assert len(depot.exemplaires_du_document(1)) == 2


def test_cycle_pret(depot):
    pret = depot.enregistrer_pret(
        Pret("D001-01", "E1", date(2026, 10, 1), date(2026, 10, 15)))
    assert pret.id is not None
    assert depot.pret_en_cours_de_exemplaire("D001-01") is not None
    assert len(depot.prets_en_cours_de("E1")) == 1
    depot.cloturer_pret(pret.id, date(2026, 10, 5))
    assert depot.pret_en_cours_de_exemplaire("D001-01") is None
    assert depot.compter_prets_total("E1") == 1


def test_file_attente_ordre(depot):
    depot.ajouter_reservation(Reservation(2, "E1", date(2026, 10, 1)))
    depot.ajouter_reservation(Reservation(2, "E2", date(2026, 10, 2)))
    assert [r.matricule for r in depot.file_attente(2)] == ["E1", "E2"]