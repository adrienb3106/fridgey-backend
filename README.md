**Aperçu**
- Backend FastAPI pour gérer utilisateurs, groupes, produits, stocks et mouvements.
- Base de données MySQL/MariaDB via SQLAlchemy.
- Deux familles de tests:
  - TU: tests rapides en SQLite mémoire (dépendances surchargées)
  - TV: tests de validation contre la vraie base définie dans `app/database.py`

**Prérequis**
- Python 3.12+
- MySQL/MariaDB accessible (ex: `fridgey`)
- Outils: `pip`, `pytest`

**Installation**
- Installer les dépendances: `pip install -r fridgey-backend/requirements.txt`
- Créer un fichier `.env` à la racine `fridgey-backend/` avec:
  - `DB_USER=...`
  - `DB_PASSWORD=...`
  - `DB_HOST=localhost`
  - `DB_PORT=3306`
  - `DB_NAME=fridgey`

**Lancement API**
- Démarrer le serveur: `cd fridgey-backend && uvicorn app.main:app --reload`
- Swagger: `http://127.0.0.1:8000/docs`

**Endpoints**
- Users:
  - POST `/users/` (create)
  - GET `/users/` (list)
  - GET `/users/{user_id}` (get)
  - DELETE `/users/{user_id}` (delete)
- Groups:
  - POST `/groups/` (create)
  - GET `/groups/` (list)
  - GET `/groups/{group_id}` (get)
  - DELETE `/groups/{group_id}` (delete)
  - POST `/groups/add_user` (link user to group, body: `user_id`, `group_id`, `role`)
  - GET `/groups/{group_id}/users` (list group users)
  - DELETE `/groups/{group_id}/users/{user_id}` (unlink user from group)
- Items:
  - POST `/items/` (create)
  - GET `/items/` (list)
  - GET `/items/{item_id}` (get)
  - DELETE `/items/{item_id}` (delete)
- Stocks:
  - POST `/stocks/` (create; crée un mouvement initial)
  - GET `/stocks/` (list)
  - GET `/stocks/{stock_id}` (get)
  - PUT `/stocks/{stock_id}?change=<float>` (maj `remaining_quantity` et création d’un mouvement)
  - DELETE `/stocks/{stock_id}` (delete)
- Movements:
  - GET `/movements/` (list all)
  - GET `/movements/stock/{stock_id}` (list by stock)
  - GET `/movements/{movement_id}` (get)

**Données de test (TV)**
- Fichier seed: `fridgey-backend/tests/test_data.sql`
- Utilisé par les tests TV pour insérer des données cohérentes dans une transaction éphémère.

**Tests**
- TU (SQLite en mémoire):
  - Commande: `pytest -q fridgey-backend/tests/TU`
  - Caractéristiques: base en mémoire partagée, `get_db` surchargé, tables créées/détruites par test.
- TV (base MySQL réelle):
  - Prérequis: `.env` valide, base et tables existantes.
  - Comportement: TRUNCATE des tables, seed via `tests/test_data.sql`, transaction rollback en fin de test.
  - Commandes:
    - Tous les TV: `pytest -q -m tv` ou `pytest -q fridgey-backend/tests/TV`
    - Un test précis: `pytest fridgey-backend/tests/TV/test_groups_tv.py::test_groups_list_and_members -vv`

**Détails d’implémentation**
- Gestion des décimaux:
  - `PUT /stocks/{id}` convertit `change` en `Decimal` pour éviter les erreurs `Decimal + float`.
- Intégrité référentielle:
  - Relation `Stock -> StockMovement` avec `cascade="all, delete-orphan"` côté ORM et `ON DELETE CASCADE` côté FK.
- Avertissements Pydantic v2:
  - Les modèles utilisent encore `Config.orm_mode`; ces warnings sont non bloquants. Migration possible vers `from_attributes=True` + `.model_dump()`.

**Dépannage**
- TV échouent au seed: vérifier que les tables existent et que les `TRUNCATE` sont autorisés (droits SQL), et que `DB_NAME` pointe bien sur la base cible.
- Erreurs de connexion: vérifier les variables `.env` et l’accessibilité du serveur MySQL.
