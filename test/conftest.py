from datetime import date
import pytest

from depot_sqlite import DepotSqlite
from modeles import Document, Exemplaire, Adherent
from service import ServiceBibliotheque


@pytest.fixture
def depot():
    d = DepotSqlite(":memory:")
    # Document 1 : 2 exemplaires ; documents 2 et 3 : 1 exemplaire
    for titre, auteur, nb in [("Les Misérables", "Victor Hugo", 2),
                              ("Clean Code", "Robert C. Martin", 1),
                              ("Candide", "Voltaire", 1)]:
        doc = d.ajouter_document(Document(None, titre, auteur, 2000, "Test"))
        for n in range(1, nb + 1):
            d.ajouter_exemplaire(Exemplaire(f"D{doc.id:03d}-{n:02d}", doc.id))
    for m in ("E1", "E2", "E3"):
        d.ajouter_adherent(Adherent(m, f"Adhérent {m}"))
    return d


@pytest.fixture
def jour():
    """Date modifiable : jour['d'] = date(...) pour simuler le temps."""
    return {"d": date(2026, 10, 1)}


@pytest.fixture
def service(depot, jour):
    return ServiceBibliotheque(depot, aujourdhui=lambda: jour["d"])