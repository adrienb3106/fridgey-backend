import os
from pathlib import Path

import pytest
from sqlalchemy import text, create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.main import app
from app.database import Base
from app.routers import users as users_router
from app.routers import groups as groups_router
from app.routers import items as items_router
from app.routers import stocks as stocks_router
from app.routers import stock_movements as movements_router


def _read_sql_file(filepath: str) -> list[str]:
    content = Path(filepath).read_text(encoding="utf-8")
    # Remove USE statements and split by ;
    lines = []
    for raw in content.splitlines():
        line = raw.strip()
        if not line or line.startswith("--") or line.upper().startswith("USE "):
            continue
        lines.append(raw)
    sql = "\n".join(lines)
    statements = [s.strip() for s in sql.split(";") if s.strip()]
    return statements


def _seed_database(connection):
    sql_path = Path(__file__).resolve().parents[1] / "test_data.sql"
    if not sql_path.exists():
        return
    stmts = _read_sql_file(str(sql_path))
    for stmt in stmts:
        connection.execute(text(stmt))


@pytest.fixture(scope="function")
def tv_db():
    """Connecte une base dédiée aux TV (test DB), jamais la base de prod.

    - Si TEST_DATABASE_URL est défini, l'utilise tel quel.
    - Sinon, construit une URL MySQL à partir des variables .env et crée
      la base `<DB_NAME>_test` (ou `fridgey_test` par défaut) si elle n'existe pas.
    - Crée le schéma (tables) si absent.
    - Isole chaque test par transaction + DELETE transactionnels.
    """
    test_url = os.getenv("TEST_DATABASE_URL")
    if not test_url:
        db_user = os.getenv("DB_USER", "root")
        db_password = os.getenv("DB_PASSWORD", "")
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = os.getenv("DB_PORT", "3306")
        base_name = os.getenv("DB_NAME", "fridgey")
        test_name = os.getenv("DB_NAME_TEST", f"{base_name}_test")

        server_url = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}"
        try:
            admin_engine = create_engine(server_url)
            with admin_engine.connect() as admin_conn:
                admin_conn.execute(text(f"CREATE DATABASE IF NOT EXISTS `{test_name}` CHARACTER SET utf8mb4"))
        except SQLAlchemyError as e:
            pytest.skip(
                "Impossible de créer/accéder à la base de test. "
                "Définis TEST_DATABASE_URL ou accordes le droit CREATE DATABASE.\n"
                f"Détail: {e}"
            )
        test_url = f"{server_url}/{test_name}"

    # Create engine for test DB
    test_engine = create_engine(test_url)

    # Ensure schema is present
    try:
        Base.metadata.create_all(bind=test_engine)
    except SQLAlchemyError as e:
        pytest.skip(f"Impossible de créer les tables sur la base de test: {e}")

    # Open connection + begin transaction for isolation
    try:
        connection = test_engine.connect()
        trans = connection.begin()
    except SQLAlchemyError as e:
        pytest.skip(f"Base de test indisponible: {e}")

    # Clean tables inside the transaction (safe, rolled back at teardown)
    try:
        connection.execute(text("SET FOREIGN_KEY_CHECKS=0"))
        # Delete in FK-safe order
        connection.execute(text("DELETE FROM stock_movements"))
        connection.execute(text("DELETE FROM stocks"))
        connection.execute(text("DELETE FROM user_groups"))
        connection.execute(text("DELETE FROM items"))
        connection.execute(text("DELETE FROM users"))
        connection.execute(text("DELETE FROM groups"))
        # Reset AUTO_INCREMENT within this transaction
        for table in ["users", "groups", "items", "stocks", "stock_movements"]:
            connection.execute(text(f"ALTER TABLE {table} AUTO_INCREMENT = 1"))
        connection.execute(text("SET FOREIGN_KEY_CHECKS=1"))
    except SQLAlchemyError:
        trans.rollback()
        connection.close()
        pytest.skip("Impossible de nettoyer/initialiser la base de test pour les TV.")

    # Seed with test data (transactional)
    _seed_database(connection)

    yield connection

    # Rollback seed + test writes
    trans.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(tv_db):
    # Bind a sessionmaker to the transaction connection
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=tv_db)
    db = TestingSessionLocal()

    def override_get_db():
        # Yield the same session across requests (managed by outer transaction)
        try:
            yield db
        finally:
            # Don't close here, we close once per test in teardown
            pass

    # Override dependencies
    app.dependency_overrides[users_router.get_db] = override_get_db
    app.dependency_overrides[groups_router.get_db] = override_get_db
    app.dependency_overrides[items_router.get_db] = override_get_db
    app.dependency_overrides[stocks_router.get_db] = override_get_db
    app.dependency_overrides[movements_router.get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    # Teardown
    db.close()
    app.dependency_overrides.clear()
