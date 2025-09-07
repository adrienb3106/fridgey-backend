from sqlalchemy import inspect
from app.database import engine

def test_users_table_schema():
    inspector = inspect(engine)
    columns = [col["name"] for col in inspector.get_columns("users")]
    expected = ["id", "name", "email", "created_at"]
    for col in expected:
        assert col in columns, f"Colonne manquante dans users: {col}"


def test_groups_table_schema():
    inspector = inspect(engine)
    columns = [col["name"] for col in inspector.get_columns("groups")]
    expected = ["id", "name", "created_at"]
    for col in expected:
        assert col in columns, f"Colonne manquante dans groups: {col}"


def test_user_groups_table_schema():
    inspector = inspect(engine)
    columns = [col["name"] for col in inspector.get_columns("user_groups")]
    expected = ["user_id", "group_id", "role"]
    for col in expected:
        assert col in columns, f"Colonne manquante dans user_groups: {col}"


def test_items_table_schema():
    inspector = inspect(engine)
    columns = [col["name"] for col in inspector.get_columns("items")]
    expected = ["id", "name", "is_food", "unit", "created_at"]
    for col in expected:
        assert col in columns, f"Colonne manquante dans items: {col}"


def test_stocks_table_schema():
    inspector = inspect(engine)
    columns = [col["name"] for col in inspector.get_columns("stocks")]
    expected = [
        "id",
        "item_id",
        "user_id",
        "group_id",
        "expiration_date",
        "initial_quantity",
        "remaining_quantity",
        "lot_count",
        "created_at",
        "updated_at",
    ]
    for col in expected:
        assert col in columns, f"Colonne manquante dans stocks: {col}"


def test_stock_movements_table_schema():
    inspector = inspect(engine)
    columns = [col["name"] for col in inspector.get_columns("stock_movements")]
    expected = ["id", "stock_id", "change_quantity", "note", "created_at"]
    for col in expected:
        assert col in columns, f"Colonne manquante dans stock_movements: {col}"
