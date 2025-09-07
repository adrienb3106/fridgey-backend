import pytest


@pytest.mark.tv
def test_items_list_and_get(client):
    r_list = client.get("/items/")
    assert r_list.status_code == 200
    items = r_list.json()
    names = {i["name"] for i in items}
    assert {"Beurre", "Lait"}.issubset(names)

    # Get first item (Beurre -> id=1 in seed)
    r_get = client.get("/items/1")
    assert r_get.status_code == 200
    assert r_get.json()["name"] == "Beurre"

