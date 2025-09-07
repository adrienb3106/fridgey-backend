import pytest


@pytest.mark.tv
def test_groups_list_and_members(client):
    r_list = client.get("/groups/")
    assert r_list.status_code == 200
    groups = r_list.json()
    names = {g["name"] for g in groups}
    assert {"Famille", "Coloc", "Amis"}.issubset(names)

    # Users in group 1 (Famille): Alice (1) admin, Bob (2) member
    r_users = client.get("/groups/1/users")
    assert r_users.status_code == 200
    user_ids = {u["id"] for u in r_users.json()}
    assert {1, 2}.issubset(user_ids)

    # Add and remove a user without persisting thanks to outer transaction
    r_add = client.post(
        "/groups/add_user",
        json={"user_id": 3, "group_id": 1, "role": "member"},
    )
    assert r_add.status_code == 200

    r_rm = client.delete("/groups/1/users/3")
    assert r_rm.status_code == 200

