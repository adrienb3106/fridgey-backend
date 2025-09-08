def test_groups_crud_and_membership(client):
    # Create a user for membership tests
    ru = client.post("/users/", json={"name": "Bob", "email": "bob@example.com"})
    assert ru.status_code == 200
    user_id = ru.json()["id"]

    # Create group
    rg = client.post("/groups/", json={"name": "Famille"})
    assert rg.status_code == 200
    group = rg.json()
    group_id = group["id"]

    # List groups
    r_list = client.get("/groups/")
    assert r_list.status_code == 200
    assert any(g["id"] == group_id for g in r_list.json())

    # Get group
    r_get = client.get(f"/groups/{group_id}")
    assert r_get.status_code == 200
    assert r_get.json()["name"] == "Famille"

    # Not found
    r_nf = client.get("/groups/9999")
    assert r_nf.status_code == 404

    # Add user to group
    rl = client.post(
        "/groups/add_user",
        json={"user_id": user_id, "group_id": group_id, "role": "admin"},
    )
    assert rl.status_code == 200

    # Adding again should fail
    rl_dup = client.post(
        "/groups/add_user",
        json={"user_id": user_id, "group_id": group_id, "role": "admin"},
    )
    assert rl_dup.status_code == 400

    # Get group users
    r_users = client.get(f"/groups/{group_id}/users")
    assert r_users.status_code == 200
    users = r_users.json()
    assert any(u["id"] == user_id for u in users)

    # Remove user from group then delete the group
    r_rm = client.delete(f"/groups/{group_id}/users/{user_id}")
    assert r_rm.status_code == 200

    # Delete group
    r_del = client.delete(f"/groups/{group_id}")
    assert r_del.status_code == 200

    # Get after delete -> 404
    r_get2 = client.get(f"/groups/{group_id}")
    assert r_get2.status_code == 404


def test_groups_delete_without_links(client):
    # Create group
    rg = client.post("/groups/", json={"name": "Jetable"})
    assert rg.status_code == 200
    gid = rg.json()["id"]

    # Delete group (no user link)
    r_del = client.delete(f"/groups/{gid}")
    assert r_del.status_code == 200

    # After delete -> 404
    r_get = client.get(f"/groups/{gid}")
    assert r_get.status_code == 404


def test_group_delete_with_existing_link_returns_400(client):
    # Create a user and a group
    ru = client.post("/users/", json={"name": "Eve", "email": "eve@example.com"})
    assert ru.status_code == 200
    uid = ru.json()["id"]

    rg = client.post("/groups/", json={"name": "Liens"})
    assert rg.status_code == 200
    gid = rg.json()["id"]

    # Link user to group
    rl = client.post(
        "/groups/add_user",
        json={"user_id": uid, "group_id": gid, "role": "member"},
    )
    assert rl.status_code == 200

    # Attempt to delete the group while link exists -> 409 explicite
    r_del = client.delete(f"/groups/{gid}")
    assert r_del.status_code == 409
