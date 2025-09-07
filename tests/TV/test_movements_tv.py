import pytest


@pytest.mark.tv
def test_movements_list_and_by_stock(client):
    # List all
    r_all = client.get("/movements/")
    assert r_all.status_code == 200
    movs = r_all.json()
    assert len(movs) >= 8

    # List for stock 1 (Alice's beurre) -> at least 2 movements
    r_s1 = client.get("/movements/stock/1")
    assert r_s1.status_code == 200
    m1 = r_s1.json()
    assert len(m1) >= 2
    notes = {m["note"] for m in m1}
    assert "Stock initial" in notes

