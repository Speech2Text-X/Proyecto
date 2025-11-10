def _setup_transcription(client):
    u = client.post("/users", json={"email": "frank@example.com", "name": "Frank", "pwd_hash": "x", "role": "user"}).json()
    p = client.post("/projects", json={"owner_id": u["id"], "name": "ShareProj"}).json()
    a = client.post("/audio", json={"project_id": p["id"], "s3_uri": "/audios/audio.mp3"}).json()
    t = client.post("/transcriptions", json={"audio_id": a["id"]}).json()
    return t["id"]


def test_shares_flow(client):
    tid = _setup_transcription(client)

    token = "tok123"
    # Create
    r = client.post("/shares", json={"transcription_id": tid, "token": token, "kind": "private"})
    assert r.status_code == 200, r.text
    share = r.json()
    sid = share["id"]

    # Resolve
    r = client.get(f"/shares/resolve/{token}")
    assert r.status_code == 200

    # Update
    r = client.patch(f"/shares/{sid}", json={"kind": "public", "can_edit": True})
    assert r.status_code == 200
    assert r.json()["kind"] == "public"

    # Cleanup (no expirados, debería ser >=0)
    r = client.post("/shares/cleanup")
    assert r.status_code == 200

    # Delete
    r = client.delete(f"/shares/{sid}")
    assert r.status_code == 200

def test_shares_expires_and_cleanup(client):
    tid = _setup_transcription(client)
    import datetime as dt
    past = (dt.datetime.utcnow() - dt.timedelta(seconds=5)).isoformat() + "Z"
    future = (dt.datetime.utcnow() + dt.timedelta(seconds=3600)).isoformat() + "Z"

    r = client.post("/shares", json={"transcription_id": tid, "token": "pasttok", "kind": "private", "expires_at": past})
    assert r.status_code == 200
    r = client.get("/shares/resolve/pasttok")
    assert r.status_code == 200
    r = client.post("/shares/cleanup")
    assert r.status_code == 200
    r = client.get("/shares/resolve/pasttok")
    assert r.status_code == 404

    r = client.post("/shares", json={"transcription_id": tid, "token": "futuretok", "kind": "private", "expires_at": future})
    assert r.status_code == 200
    r = client.get("/shares/resolve/futuretok")
    assert r.status_code == 200

def test_share_create_invalid_kind(client):
    tid = _setup_transcription(client)
    r = client.post("/shares", json={"transcription_id": tid, "token": "badkind", "kind": "invalid"})
    assert r.status_code == 400

def test_share_token_extreme_size(client):
    tid = _setup_transcription(client)
    token = "t" * 5000
    r = client.post("/shares", json={"transcription_id": tid, "token": token, "kind": "private"})
    assert r.status_code == 200

def test_share_created_by_null_on_user_delete(client):
    from app import repo_users
    creator = client.post("/users", json={"email": "creator@example.com", "pwd_hash": "x"}).json()
    owner = client.post("/users", json={"email": "owner@example.com", "pwd_hash": "x"}).json()
    p = client.post("/projects", json={"owner_id": owner["id"], "name": "P"}).json()
    a = client.post("/audio", json={"project_id": p["id"], "s3_uri": "/audios/audio.mp3"}).json()
    t = client.post("/transcriptions", json={"audio_id": a["id"]}).json()
    r = client.post("/shares", json={"transcription_id": t["id"], "token": "creatortok", "kind": "private", "created_by": creator["id"]})
    assert r.status_code == 200
    repo_users.delete_user(creator["id"])
    r = client.get("/shares/resolve/creatortok")
    assert r.status_code == 200
    assert r.json()["created_by"] is None
def test_shares_not_found_paths(client):
    r = client.get("/shares/resolve/does-not-exist")
    assert r.status_code == 404
    r = client.patch("/shares/00000000-0000-0000-0000-000000000000", json={"kind": "public"})
    assert r.status_code == 404
    r = client.delete("/shares/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404

def test_share_duplicate_token(client):
    tid = _setup_transcription(client)
    r1 = client.post("/shares", json={"transcription_id": tid, "token": "dup", "kind": "private"})
    assert r1.status_code == 200
    r2 = client.post("/shares", json={"transcription_id": tid, "token": "dup", "kind": "private"})
    assert r2.status_code == 400
