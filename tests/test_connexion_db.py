from sqlalchemy.exc import OperationalError
from sqlalchemy import text
from app.database import engine

def test_database_connection():
    """Vérifie que la connexion DB fonctionne avec SELECT 1"""
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            assert result.scalar() == 1
    except OperationalError:
        assert False, "La connexion à la base de données a échoué"
