def test_items_crud_flow(client):
    # Create
    ri = client.post(
        "/items/",
        json={"name": "Pomme", "is_food": True, "unit": "kg"},
    )
    assert ri.status_code == 200
    item_id = ri.json()["id"]

    # List
    r_list = client.get("/items/")
    assert r_list.status_code == 200
    assert any(i["id"] == item_id for i in r_list.json())

    # Get
    r_get = client.get(f"/items/{item_id}")
    assert r_get.status_code == 200
    assert r_get.json()["name"] == "Pomme"

    # Not found
    r_nf = client.get("/items/9999")
    assert r_nf.status_code == 404

    # Delete
    r_del = client.delete(f"/items/{item_id}")
    assert r_del.status_code == 200

    # After delete -> 404
    r_get2 = client.get(f"/items/{item_id}")
    assert r_get2.status_code == 404

