def test_create_and_get_user(client):
    payload = {
        "email": "alice@example.com",
        "name": "Alice",
        "pwd_hash": "x",
        "role": "user",
    }
    r = client.post("/users", json=payload)
    assert r.status_code == 200, r.text
    user = r.json()
    assert user["email"] == payload["email"]
    uid = user["id"]

    r = client.get(f"/users/{uid}")
    assert r.status_code == 200
    fetched = r.json()
    assert fetched["id"] == uid
    assert fetched["email"] == payload["email"]

def test_user_invalid_email(client):
    r = client.post("/users", json={"email": "not-an-email", "pwd_hash": "x"})
    assert r.status_code == 422

def test_user_duplicate_email(client):
    p = {"email": "dup@example.com", "pwd_hash": "x"}
    r1 = client.post("/users", json=p)
    assert r1.status_code == 200
    r2 = client.post("/users", json=p)
    assert r2.status_code == 400

def test_user_get_not_found(client):
    r = client.get("/users/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404

def test_user_uppercase_email_accepted(client):
    r = client.post("/users", json={"email": "ALICE@EXAMPLE.COM", "pwd_hash": "x"})
    assert r.status_code == 200

def test_user_missing_pwd_hash(client):
    r = client.post("/users", json={"email": "nohash@example.com"})
    assert r.status_code == 422

def test_user_invalid_role(client):
    r = client.post("/users", json={"email": "rolebad@example.com", "pwd_hash": "x", "role": "superuser"})
    assert r.status_code == 400
