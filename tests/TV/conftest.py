import os
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.main import app
from app.database import engine, Base
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
    # Try to connect to the real DB
    try:
        connection = engine.connect()
        # Begin a transaction for isolation
        trans = connection.begin()
    except SQLAlchemyError as e:
        pytest.skip(f"DB indisponible pour les TV: {e}")

    # Optional: ensure schema exists (no-op if already present)
    # Base.metadata.create_all(bind=connection)

    # Clean tables using TRUNCATE and reset autoincrement
    try:
        connection.execute(text("SET FOREIGN_KEY_CHECKS=0"))
        for table in [
            "stock_movements",
            "stocks",
            "user_groups",
            "items",
            "users",
            "groups",
        ]:
            connection.execute(text(f"TRUNCATE TABLE {table}"))
        connection.execute(text("SET FOREIGN_KEY_CHECKS=1"))
    except SQLAlchemyError:
        # If tables don't exist or other issues, rollback and skip
        trans.rollback()
        connection.close()
        pytest.skip("Impossible de nettoyer/initialiser la base pour les TV.")

    # Seed with test data
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
