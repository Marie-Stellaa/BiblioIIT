from datetime import date
import pytest
from service import ErreurBiblio


def test_emprunter(service, depot):
    pret = service.emprunter("D001-01", "E1")
    assert pret.date_retour_prevue == date(2026, 10, 15)
    assert depot.obtenir_exemplaire("D001-01").statut == "emprunte"


def test_exemplaire_deja_emprunte(service):
    service.emprunter("D001-01", "E1")
    with pytest.raises(ErreurBiblio, match="déjà emprunté"):
        service.emprunter("D001-01", "E2")


def test_choix_automatique_de_l_exemplaire(service):
    service.emprunter_document(1, "E1")
    p = service.emprunter_document(1, "E2")
    assert p.code_barres == "D001-02"
    with pytest.raises(ErreurBiblio, match="Aucun exemplaire"):
        service.emprunter_document(1, "E3")


def test_inconnus(service):
    with pytest.raises(ErreurBiblio):
        service.emprunter("D999-01", "E1")
    with pytest.raises(ErreurBiblio):
        service.emprunter("D001-01", "X")


def test_limite_de_prets(service):
    service.emprunter("D001-01", "E1")
    service.emprunter("D001-02", "E1")
    service.emprunter("D002-01", "E1")
    with pytest.raises(ErreurBiblio, match="limite"):
        service.emprunter("D003-01", "E1")


def test_exemplaire_perdu(service):
    service.changer_etat("D001-01", "perdu")
    with pytest.raises(ErreurBiblio, match="pas empruntable"):
        service.emprunter("D001-01", "E1")


def test_rendre_non_emprunte(service):
    with pytest.raises(ErreurBiblio, match="n'est pas emprunté"):
        service.rendre("D001-01")


def test_rendre_dans_les_temps(service, depot):
    service.emprunter("D001-01", "E1")
    r = service.rendre("D001-01")
    assert r.jours_retard == 0 and r.suspendu_jusqu is None
    assert depot.obtenir_exemplaire("D001-01").statut == "disponible"


def test_retard_et_suspension(service, jour):
    service.emprunter("D002-01", "E1")
    jour["d"] = date(2026, 10, 20)               # 5 jours de retard
    assert len(service.retards()) == 1
    with pytest.raises(ErreurBiblio, match="retard"):
        service.emprunter("D001-01", "E1")       # prêt en retard à rendre
    r = service.rendre("D002-01")
    assert r.jours_retard == 5
    assert r.suspendu_jusqu == date(2026, 10, 30)
    with pytest.raises(ErreurBiblio, match="suspendu"):
        service.emprunter("D001-01", "E1")
    jour["d"] = date(2026, 10, 31)
    service.emprunter("D001-01", "E1")           # suspension terminée


def test_prolonger(service):
    service.emprunter("D001-01", "E1")
    pret = service.prolonger("D001-01")
    assert pret.date_retour_prevue == date(2026, 10, 22)
    with pytest.raises(ErreurBiblio, match="limite"):
        service.prolonger("D001-01")


def test_prolonger_refuse_si_reserve(service):
    service.emprunter("D002-01", "E1")
    service.reserver(2, "E2")
    with pytest.raises(ErreurBiblio, match="réservé"):
        service.prolonger("D002-01")


def test_reserver_refuse_si_disponible(service):
    with pytest.raises(ErreurBiblio, match="disponible"):
        service.reserver(2, "E2")


def test_file_d_attente_complete(service, depot):
    service.emprunter("D002-01", "E1")
    _, position = service.reserver(2, "E2")
    assert position == 1
    _, position = service.reserver(2, "E3")
    assert position == 2
    with pytest.raises(ErreurBiblio, match="déjà réservé"):
        service.reserver(2, "E2")

    r = service.rendre("D002-01")
    assert r.reservation_servie.matricule == "E2"
    assert depot.obtenir_exemplaire("D002-01").statut == "reserve"
    with pytest.raises(ErreurBiblio, match="réservé"):
        service.emprunter("D002-01", "E3")       # pas son tour

    service.emprunter_document(2, "E2")          # le 1er de la file l'emprunte
    assert depot.obtenir_exemplaire("D002-01").statut == "emprunte"


def test_recherche_avec_disponibilite(service):
    service.emprunter("D001-01", "E1")
    (r,) = service.rechercher("misérables")
    assert (r.total, r.disponibles) == (2, 1)


def test_fiche(service):
    service.emprunter("D001-01", "E1")
    f = service.fiche("E1")
    assert f.total_prets == 1 and len(f.prets) == 1 and not f.suspendu


def test_ajouter_document_et_exemplaires(service, depot):
    doc = service.ajouter_document("Titre", "Auteur", 2020, "Test", 2)
    assert len(depot.exemplaires_du_document(doc.id)) == 2
    service.ajouter_exemplaire(doc.id)
    assert len(depot.exemplaires_du_document(doc.id)) == 3