from sqlalchemy import inspect
from app.database import engine

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
