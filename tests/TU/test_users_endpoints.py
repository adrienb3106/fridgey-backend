def test_users_crud_flow(client):
    # Create
    payload = {"name": "Alice", "email": "alice@example.com"}
    r = client.post("/users/", json=payload)
    assert r.status_code == 200
    user = r.json()
    assert user["id"] > 0
    user_id = user["id"]

    # Duplicate email should fail
    r_dup = client.post("/users/", json=payload)
    assert r_dup.status_code == 400

    # List
    r_list = client.get("/users/")
    assert r_list.status_code == 200
    assert any(u["id"] == user_id for u in r_list.json())

    # Get
    r_get = client.get(f"/users/{user_id}")
    assert r_get.status_code == 200
    assert r_get.json()["email"] == "alice@example.com"

    # Not found
    r_nf = client.get("/users/9999")
    assert r_nf.status_code == 404

    # Delete
    r_del = client.delete(f"/users/{user_id}")
    assert r_del.status_code == 200

    # Get after delete -> 404
    r_get2 = client.get(f"/users/{user_id}")
    assert r_get2.status_code == 404

