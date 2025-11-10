def _setup_transcription(client):
    u = client.post("/users", json={"email": "eve@example.com", "name": "Eve", "pwd_hash": "x", "role": "user"}).json()
    p = client.post("/projects", json={"owner_id": u["id"], "name": "S"}).json()
    a = client.post("/audio", json={"project_id": p["id"], "s3_uri": "/audios/audio.mp3"}).json()
    t = client.post("/transcriptions", json={"audio_id": a["id"]}).json()
    return t["id"]


def test_segments_crud(client):
    tid = _setup_transcription(client)

    # Create segment
    r = client.post(f"/segments/{tid}", json={"start_ms": 0, "end_ms": 1000, "text": "Hello"})
    assert r.status_code == 200
    seg_id = r.json()["id"]
    assert seg_id

    # List
    r = client.get(f"/segments/{tid}")
    assert r.status_code == 200
    items = r.json()
    assert any(s["id"] == seg_id for s in items)

    # Delete all
    r = client.delete(f"/segments/{tid}")
    assert r.status_code == 200
    assert r.json()["deleted"] >= 1

def _tid(client):
    u = client.post("/users", json={"email": "sedge@example.com", "pwd_hash": "x"}).json()
    p = client.post("/projects", json={"owner_id": u["id"], "name": "S"}).json()
    a = client.post("/audio", json={"project_id": p["id"], "s3_uri": "/audios/audio.mp3"}).json()
    t = client.post("/transcriptions", json={"audio_id": a["id"]}).json()
    return t["id"]

def test_segments_invalid_range_allowed_and_list_pagination(client):
    tid = _tid(client)
    r = client.post(f"/segments/{tid}", json={"start_ms": 1000, "end_ms": 0, "text": "x"})
    assert r.status_code == 200
    r = client.get(f"/segments/{tid}?limit=1&offset=1000")
    assert r.status_code == 200
    assert r.json() == []

def test_segments_negative_and_equal_and_sort_order(client):
    tid = _tid(client)
    client.post(f"/segments/{tid}", json={"start_ms": 500, "end_ms": 500, "text": "eq"})
    client.post(f"/segments/{tid}", json={"start_ms": -100, "end_ms": 0, "text": "neg"})
    client.post(f"/segments/{tid}", json={"start_ms": 0, "end_ms": 10, "text": "zero"})
    items = client.get(f"/segments/{tid}").json()
    starts = [s["start_ms"] for s in items]
    assert starts == sorted(starts)
