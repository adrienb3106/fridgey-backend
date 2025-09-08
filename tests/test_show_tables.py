import pytest
from sqlalchemy import inspect, text
from sqlalchemy.exc import OperationalError
from app.database import engine

# Skip ce module si la DB n'est pas accessible
try:
    with engine.connect() as _c:
        _c.execute(text("SELECT 1"))
except OperationalError:
    pytest.skip("Base non accessible: skip tests de tables en environnement local", allow_module_level=True)

def test_tables_exist():
    """Vérifie que toutes les tables du MCD existent déjà dans la base 'fridgey'"""
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    expected_tables = [
        "users",
        "groups",
        "user_groups",
        "items",
        "stocks",
        "stock_movements"
    ]

    # Vérifie que chaque table attendue existe
    for table in expected_tables:
        assert table in tables, f"La table {table} est manquante dans la base"
