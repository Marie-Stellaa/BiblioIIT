from datetime import date
import regles


def test_date_retour_prevue():
    assert regles.date_retour_prevue(date(2026, 10, 1)) == date(2026, 10, 15)


def test_limite_de_prets():
    assert regles.peut_emprunter(2)
    assert not regles.peut_emprunter(regles.MAX_PRETS_PAR_ADHERENT)


def test_retard():
    prevu = date(2026, 10, 15)
    assert not regles.est_en_retard(prevu, date(2026, 10, 15))
    assert regles.jours_de_retard(prevu, date(2026, 10, 18)) == 3


def test_suspension():
    assert regles.duree_suspension(5) == 10
    assert regles.est_suspendu(date(2026, 10, 30), date(2026, 10, 29))
    assert not regles.est_suspendu(date(2026, 10, 30), date(2026, 10, 30))
    assert not regles.est_suspendu(None, date(2026, 10, 1))


def test_prolongation():
    assert regles.peut_prolonger(0)
    assert not regles.peut_prolonger(regles.MAX_PROLONGATIONS)
    assert regles.date_apres_prolongation(date(2026, 10, 15)) == date(2026, 10, 22)