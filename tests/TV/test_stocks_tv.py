import pytest


@pytest.mark.tv
def test_stocks_list_get_and_update(client):
    # List stocks
    r_list = client.get("/stocks/")
    assert r_list.status_code == 200
    stocks = r_list.json()
    assert any(s["id"] == 2 for s in stocks)  # stock lait group 1

    # Get stock 2 -> remaining 4.00
    r_get = client.get("/stocks/2")
    assert r_get.status_code == 200
    assert float(r_get.json()["remaining_quantity"]) == 4.0

    # Update stock 2 by -1 (should become 3.0)
    r_upd = client.put("/stocks/2", params={"change": -1})
    assert r_upd.status_code == 200
    assert float(r_upd.json()["remaining_quantity"]) == 3.0

