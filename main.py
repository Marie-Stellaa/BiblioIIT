from console import Console
from depot_sqlite import DepotSqlite
from donnees import charger_donnees
from service import ServiceBibliotheque

if __name__ == "__main__":
    depot = DepotSqlite("biblioiit.db")
    if depot.nombre_documents() == 0:        
        charger_donnees(depot)
    Console(ServiceBibliotheque(depot)).lancer()