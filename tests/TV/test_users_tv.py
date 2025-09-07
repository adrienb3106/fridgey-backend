import pytest


@pytest.mark.tv
def test_users_list_and_get(client):
    # Seed provides 3 users
    r_list = client.get("/users/")
    assert r_list.status_code == 200
    users = r_list.json()
    assert len(users) >= 3
    names = {u["name"] for u in users}
    assert {"Alice", "Bob", "Charlie"}.issubset(names)

    # Get Alice (id=1)
    r_get = client.get("/users/1")
    assert r_get.status_code == 200
    assert r_get.json()["name"] == "Alice"

