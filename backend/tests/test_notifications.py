def _setup_transcription(client):
    u = client.post("/users", json={"email": "gina@example.com", "name": "Gina", "pwd_hash": "x", "role": "user"}).json()
    p = client.post("/projects", json={"owner_id": u["id"], "name": "NotifProj"}).json()
    a = client.post("/audio", json={"project_id": p["id"], "s3_uri": "/audios/audio.mp3"}).json()
    t = client.post("/transcriptions", json={"audio_id": a["id"]}).json()
    return t["id"]


def test_notifications_flow(client):
    tid = _setup_transcription(client)

    payload = {"transcription_id": tid, "type": "email", "target": "test@example.com"}
    r = client.post("/notifications", json=payload)
    assert r.status_code == 200, r.text
    n = r.json()
    nid = n["id"]

    r = client.get(f"/notifications?transcription_id={tid}")
    assert r.status_code == 200
    assert any(x["id"] == nid for x in r.json())

    r = client.post(f"/notifications/{nid}/status", json={"status": "sent"})
    assert r.status_code == 200
    assert r.json()["status"] == "sent"

    r = client.delete(f"/notifications/{nid}")
    assert r.status_code == 200

def test_notification_invalid_type_and_status(client):
    tid = _setup_transcription(client)
    r = client.post("/notifications", json={"transcription_id": tid, "type": "foo", "target": "t"})
    assert r.status_code == 400
    r = client.post("/notifications", json={"transcription_id": tid, "type": "email", "target": "t"})
    assert r.status_code == 200
    nid = r.json()["id"]
    r = client.post(f"/notifications/{nid}/status", json={"status": "foo"})
    assert r.status_code == 400

def test_notification_list_empty_and_delete_not_found(client):
    r = client.get("/notifications?transcription_id=00000000-0000-0000-0000-000000000000")
    assert r.status_code == 200
    assert r.json() == []
    r = client.delete("/notifications/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404

def test_notifications_pagination_and_payload_large(client):
    tid = _setup_transcription(client)
    ids = []
    for i in range(3):
        r = client.post("/notifications", json={"transcription_id": tid, "type": "email", "target": f"t{i}@e.c"})
        ids.append(r.json()["id"])
    r = client.get(f"/notifications?transcription_id={tid}&limit=2&offset=1")
    assert r.status_code == 200
    assert len(r.json()) <= 2
    large_payload = {"a": "x" * 100000}
    nid = ids[0]
    r = client.post(f"/notifications/{nid}/status", json={"status": "sent", "payload": large_payload})
    assert r.status_code == 200
