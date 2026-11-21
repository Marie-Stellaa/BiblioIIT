from datetime import date
from modeles import Pret


def test_pret_en_cours():
    p = Pret("L002", "E2026-001", date(2026, 10, 1), date(2026, 10, 15))
    assert p.en_cours
    p.date_retour = date(2026, 10, 5)
    assert not p.en_cours