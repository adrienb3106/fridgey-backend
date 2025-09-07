def _create_item(client, name="Yaourt"):
    r = client.post("/items/", json={"name": name, "is_food": True, "unit": "u"})
    assert r.status_code == 200
    return r.json()["id"]


def _create_stock_and_move(client):
    item_id = _create_item(client)
    rs = client.post(
        "/stocks/",
        json={
            "item_id": item_id,
            "user_id": None,
            "group_id": None,
            "expiration_date": None,
            "initial_quantity": 5.0,
            "remaining_quantity": 5.0,
            "lot_count": 1,
        },
    )
    assert rs.status_code == 200
    stock_id = rs.json()["id"]

    # Create a second movement by updating quantity
    r_upd = client.put(f"/stocks/{stock_id}", params={"change": -2})
    assert r_upd.status_code == 200
    return stock_id


def test_movements_listing_and_get(client):
    stock_id = _create_stock_and_move(client)

    # List all movements (should be at least 2: initial + update)
    r_all = client.get("/movements/")
    assert r_all.status_code == 200
    all_movs = r_all.json()
    assert len(all_movs) >= 2

    # List by stock
    r_stock = client.get(f"/movements/stock/{stock_id}")
    assert r_stock.status_code == 200
    stock_movs = r_stock.json()
    assert len(stock_movs) >= 2
    first_id = stock_movs[0]["id"]

    # Get by id
    r_get = client.get(f"/movements/{first_id}")
    assert r_get.status_code == 200
    assert r_get.json()["id"] == first_id

    # Not found
    r_nf = client.get("/movements/9999")
    assert r_nf.status_code == 404
