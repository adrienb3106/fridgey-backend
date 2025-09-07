def _create_item(client, name="Lait"):
    r = client.post("/items/", json={"name": name, "is_food": True, "unit": "L"})
    assert r.status_code == 200
    return r.json()["id"]


def test_stocks_crud_and_update(client):
    # Need an item first
    item_id = _create_item(client)

    # Create stock
    rs = client.post(
        "/stocks/",
        json={
            "item_id": item_id,
            "user_id": None,
            "group_id": None,
            "expiration_date": None,
            "initial_quantity": 3.0,
            "remaining_quantity": 3.0,
            "lot_count": 1,
        },
    )
    assert rs.status_code == 200
    stock = rs.json()
    stock_id = stock["id"]

    # List
    r_list = client.get("/stocks/")
    assert r_list.status_code == 200
    assert any(s["id"] == stock_id for s in r_list.json())

    # Get
    r_get = client.get(f"/stocks/{stock_id}")
    assert r_get.status_code == 200
    assert float(r_get.json()["remaining_quantity"]) == 3.0

    # Update remaining quantity via change param (e.g., consume 1)
    r_upd = client.put(f"/stocks/{stock_id}", params={"change": -1})
    assert r_upd.status_code == 200
    assert float(r_upd.json()["remaining_quantity"]) == 2.0

    # Not found
    r_nf = client.get("/stocks/9999")
    assert r_nf.status_code == 404

    # Delete
    r_del = client.delete(f"/stocks/{stock_id}")
    assert r_del.status_code == 200

    # After delete -> 404
    r_get2 = client.get(f"/stocks/{stock_id}")
    assert r_get2.status_code == 404


def test_stock_create_with_unknown_item_returns_404(client):
    r = client.post(
        "/stocks/",
        json={
            "item_id": 9999,
            "user_id": None,
            "group_id": None,
            "expiration_date": None,
            "initial_quantity": 1.0,
            "remaining_quantity": 1.0,
            "lot_count": 1,
        },
    )
    assert r.status_code == 404
