def _user_and_project(client):
    u = client.post("/users", json={"email": "carol@example.com", "name": "Carol", "pwd_hash": "x", "role": "user"}).json()
    p = client.post("/projects", json={"owner_id": u["id"], "name": "A"}).json()
    return u, p


def test_audio_crud(client):
    _, proj = _user_and_project(client)

    # Create
    r = client.post("/audio", json={"project_id": proj["id"], "s3_uri": "/audios/audio.mp3"})
    assert r.status_code == 200, r.text
    audio = r.json()
    aid = audio["id"]

    # Get
    r = client.get(f"/audio/{aid}")
    assert r.status_code == 200
    assert r.json()["id"] == aid

    # List
    r = client.get(f"/audio?project_id={proj['id']}&limit=10&offset=0")
    assert r.status_code == 200
    assert any(a["id"] == aid for a in r.json())

def _project(client):
    u = client.post("/users", json={"email": "aedge@example.com", "pwd_hash": "x"}).json()
    return client.post("/projects", json={"owner_id": u["id"], "name": "A"}).json()

def test_audio_create_missing_fields(client):
    r = client.post("/audio", json={"project_id": "bad"})
    assert r.status_code in (400, 422)

def test_audio_get_not_found(client):
    r = client.get("/audio/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404

def test_audio_list_empty_ok(client):
    p = _project(client)
    r = client.get(f"/audio?project_id={p['id']}&limit=10&offset=0")
    assert r.status_code == 200
    assert r.json() == []

def test_audio_scheme_and_pagination_limits(client):
    _, proj = _user_and_project(client)
    r = client.post("/audio", json={"project_id": proj["id"], "s3_uri": "file:///not-used"})
    assert r.status_code == 200
    r = client.get(f"/audio?project_id={proj['id']}&limit=201")
    assert r.status_code == 422
    r = client.get(f"/audio?project_id={proj['id']}&offset=-1")
    assert r.status_code == 422

def test_delete_audio_cascade_transcriptions(client):
    from app import repo_audio_files
    u, proj = _user_and_project(client)
    r = client.post("/audio", json={"project_id": proj["id"], "s3_uri": "/audios/audio.mp3"})
    aid = r.json()["id"]
    r = client.post("/transcriptions", json={"audio_id": aid})
    tid = r.json()["id"]
    deleted = repo_audio_files.delete_audio(aid)
    assert str(deleted) == aid
    r = client.get(f"/transcriptions/{tid}")
    assert r.status_code == 404
