**Aperçu**
- Backend FastAPI pour gérer utilisateurs, groupes, produits, stocks et mouvements.
- Base de données MySQL/MariaDB via SQLAlchemy.
- Deux familles de tests:
  - TU: tests rapides sur SQLite en mémoire (dépendances surchargées)
  - TV: tests de validation sur une base de TEST dédiée (jamais la base réelle)

**Prérequis**
- Python 3.12+
- MySQL/MariaDB accessible
- Outils: `pip`, `pytest`

**Installation**
- Installer les dépendances: `pip install -r fridgey-backend/requirements.txt`
- Créer un fichier `.env` dans `fridgey-backend/` (non versionné) avec par exemple:
  - `DB_USER=...`
  - `DB_PASSWORD=...`
  - `DB_HOST=localhost`
  - `DB_PORT=3306`
  - `DB_NAME=fridgey`
  - Option tests (au choix):
    - `TEST_DATABASE_URL=mysql+pymysql://user:pass@host:3306/fridgey_test`
    - ou `DB_NAME_TEST=fridgey_test` (le nom de base de test sera créé si possible)

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
  - POST `/groups/add_user` (lier un user à un groupe; body: `user_id`, `group_id`, `role`)
  - GET `/groups/{group_id}/users` (lister les utilisateurs d’un groupe)
  - DELETE `/groups/{group_id}/users/{user_id}` (retirer un user du groupe)
- Items:
  - POST `/items/` (create)
  - GET `/items/` (list)
  - GET `/items/{item_id}` (get)
  - DELETE `/items/{item_id}` (delete)
- Stocks:
  - POST `/stocks/` (create; crée un mouvement initial)
  - GET `/stocks/` (list)
  - GET `/stocks/{stock_id}` (get)
  - PUT `/stocks/{stock_id}?change=<float>` (met à jour `remaining_quantity` + crée un mouvement)
  - DELETE `/stocks/{stock_id}` (delete)
- Movements:
  - GET `/movements/` (list all)
  - GET `/movements/stock/{stock_id}` (list by stock)
  - GET `/movements/{movement_id}` (get)

**Données de test**
- Fichier seed: `fridgey-backend/tests/test_data.sql`
- Utilisé par les tests TV pour insérer des données cohérentes dans une transaction éphémère.

**Tests**
- TU (SQLite en mémoire):
  - Commande: `pytest -q fridgey-backend/tests/TU`
  - Caractéristiques: base SQLite en mémoire partagée, `get_db` surchargé, tables créées/détruites par test.
- TV (base MySQL de TEST dédiée):
  - Ne touche jamais la base “réelle”.
  - Prérequis: `.env` avec au choix:
    - `TEST_DATABASE_URL` (prioritaire), ex: `mysql+pymysql://user:pass@host:3306/fridgey_test`
    - ou `DB_NAME_TEST` (sinon `<DB_NAME>_test` par défaut). Les tests créeront la base si possible.
  - Comportement: nettoyage par `DELETE` transactionnels (pas de TRUNCATE), seed via `tests/test_data.sql`, rollback final.
  - Commandes:
    - Tous les TV: `pytest -q -m tv` ou `pytest -q fridgey-backend/tests/TV`
    - Un test précis: `pytest fridgey-backend/tests/TV/test_groups_tv.py::test_groups_list_and_members -vv`

**Base de test (TV) et configuration**
- Variables d’environnement supportées (harmonisées):
  - `TEST_DATABASE_URL`: URL complète SQLAlchemy (recommandé pour CI/CD)
  - `DB_NAME_TEST`: nom de base de test à créer/initialiser (défaut: `<DB_NAME>_test`)
- Droits requis si `DB_NAME_TEST` est utilisé: droit `CREATE DATABASE` pour l’utilisateur MySQL, sinon créer la base manuellement.
- Les tests TV créent le schéma (tables) si absent via `Base.metadata.create_all(...)`.

**Détails d’implémentation**
- Décimaux: `PUT /stocks/{id}` convertit `change` en `Decimal` (évite `Decimal + float`).
- Intégrité référentielle: `Stock -> StockMovement` avec `cascade="all, delete-orphan"` et FK `ON DELETE CASCADE`.
- Pydantic v2: certains warnings liés à `orm_mode`; migration possible vers `from_attributes=True` + `.model_dump()`.

**Dépannage**
- TV échouent au seed: vérifier les droits `CREATE DATABASE` (ou créer manuellement la base de test), et renseigner `TEST_DATABASE_URL` ou `DB_NAME_TEST`.
- Erreurs de connexion: vérifier les variables `.env` et l’accessibilité du serveur MySQL.

**Git / secrets**
- Le fichier `.env` n’est pas versionné (voir `.gitignore`). Garder `.env.example` pour la référence si besoin.
