import pytest
from sqlalchemy.exc import OperationalError
from sqlalchemy import text
from app.database import engine


# Skip ce module si la DB n'est pas accessible dans l'environnement courant
try:
    with engine.connect() as _c:
        _c.execute(text("SELECT 1"))
except OperationalError:
    pytest.skip("Base non accessible: skip des tests de connexion en environnement local", allow_module_level=True)


def test_database_connection():
    """Vérifie que la connexion DB fonctionne avec SELECT 1"""
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        assert result.scalar() == 1
