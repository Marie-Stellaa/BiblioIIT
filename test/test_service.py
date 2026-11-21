from datetime import date
import pytest
from service import ErreurBiblio


def test_emprunter(service):
    pret = service.emprunter("L002", "E2026-001")
    assert pret.date_retour_prevue == date(2026, 10, 15)


def test_livre_deja_emprunte(service):
    service.emprunter("L002", "E2026-001")
    with pytest.raises(ErreurBiblio, match="déjà emprunté"):
        service.emprunter("L002", "E2026-002")


def test_inconnus(service):
    with pytest.raises(ErreurBiblio):
        service.emprunter("L999", "E2026-001")
    with pytest.raises(ErreurBiblio):
        service.emprunter("L002", "X")


def test_rendre(service):
    service.emprunter("L002", "E2026-001")
    service.rendre("L002")
    service.emprunter("L002", "E2026-002")  # de nouveau disponible


def test_rendre_non_emprunte(service):
    with pytest.raises(ErreurBiblio):
        service.rendre("L002")


def test_retards(service, jour):
    service.emprunter("L002", "E2026-001")
    assert service.retards() == []
    jour["d"] = date(2026, 10, 20)
    (pret, livre, jours), = service.retards()
    assert livre.code == "L002" and jours == 5