# BiblioIIT : gestion d'une bibliothèque

Application console en Python pour gérer une bibliothèque : catalogue, adhérents, prêts, retours, prolongations, réservations et sanctions de retard.

Projet academique realisé dans le cadre du cours de programmation python.

## Fonctionnalités

- **Recherche** par titre, auteur ou catégorie, avec le nombre d'exemplaires disponibles (« 2/3 dispo »)
- **Emprunt** : choix automatique d'un exemplaire disponible
- **Retour par code-barres** : le système retrouve seul l'adhérent concerné
- **Prolongation** d'un prêt (une fois, refusée si le document est réservé ou le prêt en retard)
- **Réservation** avec file d'attente « premier arrivé, premier servi »
- **Retards** et **suspension** proportionnelle au retard
- **Fiche d'un adhérent** : prêts en cours, réservations, historique
- **Gestion du catalogue** : ajout de documents, d'exemplaires, changement d'état (perdu, en réparation), inscription d'adhérents

## Installation

Prérequis : Python 3.10 ou plus récent.

```
git clone https://github.com/Marie-Stellaa/BiblioIIT
cd BiblioIIT
pip install pytest
```

Aucune autre dépendance : `sqlite3` est inclus dans Python.

## Lancer le programme

```
python main.py
```

À la première exécution, la base `biblioiit.db` est créée et remplie avec 34 documents, leurs exemplaires, 10 adhérents et quelques prêts de démonstration. Pour repartir de zéro, supprimez `biblioiit.db`.

## Lancer les tests

```
pytest
```

## Architecture

Architecture en couches : chaque module a une seule responsabilité.

```
console  →  service  →  regles + depot_sqlite  →  modeles
```

| Module | Rôle |
|---|---|
| `modeles.py` | Classes `Document`, `Exemplaire`, `Adherent`, `Pret`, `Reservation` |
| `regles.py` | Règles de gestion (durées, limites, sanctions), fonctions pures |
| `depot_sqlite.py` | Accès à la base SQLite (seul module qui connaît SQL) |
| `service.py` | Logique des parcours : emprunter, rendre, prolonger, réserver |
| `console.py` | Menu et saisies, sans logique métier |
| `donnees.py` | Catalogue de démonstration |
| `tests/` | Tests unitaires de chaque couche |

### Modèle de données

- **Document** : la notice (titre, auteur, année, catégorie)
- **Exemplaire** : un objet physique avec son code-barres (ex. `D018-02`) et son statut : disponible, emprunté, réservé, perdu, en réparation
- **Adhérent** : matricule, nom, date de fin de suspension éventuelle
- **Prêt** : exemplaire, adhérent, dates d'emprunt, de retour prévue et de retour réel
- **Réservation** : document attendu par un adhérent, avec son statut (attente, prête, terminée)

## Règles de gestion

Définies dans `regles.py`, modifiables en changeant les constantes.

| Règle | Valeur |
|---|---|
| Durée d'un prêt | 14 jours |
| Prêts simultanés maximum | 3 |
| Prolongations par prêt | 1, de 7 jours |
| Suspension après retard | 2 jours par jour de retard |

Autres règles :
- Un adhérent suspendu ou ayant un prêt en retard ne peut pas emprunter
- Une prolongation est refusée si le prêt est en retard ou si le document est réservé
- À un retour, l'exemplaire est mis de côté pour le premier de la file de réservation, sinon il redevient disponible
- Un exemplaire perdu ou en réparation n'est jamais prêtable

## Scénarios de démonstration

- **Retards** : `E2026-001` et `E2026-002` ont un livre en retard (menu 6)
- **Réservation** : *Design Patterns* n'a qu'un exemplaire, emprunté par `E2026-003` et réservé par `E2026-005`. Rendez `D034-01` (menu 3), puis faites emprunter le livre par `E2026-005` (menu 2)
- **Retour par scan** : le menu 3 accepte un code-barres, ou Entrée pour choisir dans la liste

## Limites assumées

- Pas d'annulation de réservation ni de délai d'expiration du retrait
- Pas de paiement d'amendes (sanction par suspension uniquement)
- Pas de statistiques d'emprunt
- Application mono-poste, sans multi-sites

## Intégration continue

Le fichier `.github/workflows/ci.yml` lance `pytest` à chaque push et chaque Pull Request.

## Auteur

GODE Ayekpa Epiphanie Marie-Stella Rachel
