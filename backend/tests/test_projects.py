def _create_user(client, email="bob@example.com"):
    return client.post("/users", json={"email": email, "name": "Bob", "pwd_hash": "x", "role": "user"}).json()


def test_project_crud(client):
    user = _create_user(client)

    # Create
    r = client.post("/projects", json={"owner_id": user["id"], "name": "MyProj"})
    assert r.status_code == 200, r.text
    proj = r.json()
    pid = proj["id"]
    assert proj["owner_id"] == user["id"]

    # Get
    r = client.get(f"/projects/{pid}")
    assert r.status_code == 200

    # List by owner
    r = client.get(f"/projects?owner_id={user['id']}&limit=10&offset=0")
    assert r.status_code == 200
    items = r.json()
    assert any(p["id"] == pid for p in items)

    # Update
    r = client.patch(f"/projects/{pid}", params={"owner_id": user["id"]}, json={"name": "Renamed"})
    assert r.status_code == 200
    assert r.json()["name"] == "Renamed"

    # Delete
    r = client.delete(f"/projects/{pid}", params={"owner_id": user["id"]})
    assert r.status_code == 200
    assert r.json()["deleted"] == pid

def test_project_create_owner_not_exists(client):
    r = client.post("/projects", json={"owner_id": "00000000-0000-0000-0000-000000000000", "name": "X"})
    assert r.status_code == 400

def test_project_delete_cascade(client):
    u = _create_user(client)
    r = client.post("/projects", json={"owner_id": u["id"], "name": "Cascade"})
    proj = r.json()
    pid = proj["id"]
    r = client.post("/audio", json={"project_id": pid, "s3_uri": "http://files/audio/audio.mp3"})
    audio = r.json()
    aid = audio["id"]
    r = client.post("/transcriptions", json={"audio_id": aid})
    tid = r.json()["id"]
    r = client.post(f"/segments/{tid}", json={"start_ms": 0, "end_ms": 1000, "text": "x"})
    r = client.post("/shares", json={"transcription_id": tid, "token": "cascadetok", "kind": "private"})
    share = r.json()
    sid = share["id"]
    r = client.post("/notifications", json={"transcription_id": tid, "type": "email", "target": "a@b.c"})
    n = r.json()
    nid = n["id"]

    r = client.delete(f"/projects/{pid}", params={"owner_id": u["id"]})
    assert r.status_code == 200

    r = client.get(f"/projects/{pid}")
    assert r.status_code == 404
    r = client.get(f"/audio/{aid}")
    assert r.status_code == 404
    r = client.get(f"/transcriptions/{tid}")
    assert r.status_code == 404
    r = client.get(f"/shares/resolve/cascadetok")
    assert r.status_code == 404
    r = client.get(f"/notifications?transcription_id={tid}")
    assert r.status_code == 200
    assert r.json() == []
def _user(client):
    return client.post("/users", json={"email": "pedge@example.com", "pwd_hash": "x"}).json()

def test_project_update_delete_not_owner(client):
    u1 = _user(client)
    u2 = client.post("/users", json={"email": "pedge2@example.com", "pwd_hash": "x"}).json()
    p = client.post("/projects", json={"owner_id": u1["id"], "name": "P"}).json()
    r = client.patch(f"/projects/{p['id']}", params={"owner_id": u2["id"]}, json={"name": "X"})
    assert r.status_code == 404
    r = client.delete(f"/projects/{p['id']}", params={"owner_id": u2["id"]})
    assert r.status_code == 404

def test_project_list_pagination_edges(client):
    u = _user(client)
    r = client.get(f"/projects?owner_id={u['id']}&limit=0")
    assert r.status_code == 422
    r = client.get(f"/projects?owner_id={u['id']}&limit=201")
    assert r.status_code == 422
    r = client.get(f"/projects?owner_id={u['id']}&offset=-1")
    assert r.status_code == 422

def test_project_name_empty_and_long(client):
    u = _create_user(client)
    r = client.post("/projects", json={"owner_id": u["id"], "name": ""})
    assert r.status_code == 200
    long_name = "x" * 5000
    r = client.post("/projects", json={"owner_id": u["id"], "name": long_name})
    assert r.status_code == 200
