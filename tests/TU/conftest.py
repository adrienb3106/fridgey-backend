import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base
from app.routers import users as users_router
from app.routers import groups as groups_router
from app.routers import items as items_router
from app.routers import stocks as stocks_router
from app.routers import stock_movements as movements_router


# Engine SQLite en mémoire partagé pour les tests
engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Activer les contraintes FK pour SQLite (nécessaire pour CASCADE)
from sqlalchemy import event


@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA foreign_keys=ON")
    finally:
        cursor.close()
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Override des dépendances DB pour tous les routeurs
app.dependency_overrides[users_router.get_db] = override_get_db
app.dependency_overrides[groups_router.get_db] = override_get_db
app.dependency_overrides[items_router.get_db] = override_get_db
app.dependency_overrides[stocks_router.get_db] = override_get_db
app.dependency_overrides[movements_router.get_db] = override_get_db


@pytest.fixture(scope="function")
def client():
    # Isolation de la base pour chaque test
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
