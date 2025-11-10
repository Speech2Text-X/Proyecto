from unittest.mock import patch


def _bootstrap_audio(client):
    u = client.post("/users", json={"email": "dave@example.com", "name": "Dave", "pwd_hash": "x", "role": "user"}).json()
    p = client.post("/projects", json={"owner_id": u["id"], "name": "T"}).json()
    a = client.post("/audio", json={"project_id": p["id"], "s3_uri": "http://files/audio/audio.mp3"}).json()
    return a


def test_transcription_create_and_poll(client):
    a = _bootstrap_audio(client)

    with patch("app.routers.transcriptions.process_transcription", autospec=True) as proc_mock:
        r = client.post("/transcriptions", json={"audio_id": a["id"], "mode": "batch", "temperature": 0.0, "beam_size": 5})
        assert r.status_code == 200, r.text
        t = r.json()
        assert "id" in t
        proc_mock.assert_called_once()

    tid = t["id"]
    r = client.get(f"/transcriptions/{tid}")
    assert r.status_code == 200


def test_transcription_state_transitions(client):
    a = _bootstrap_audio(client)
    r = client.post("/transcriptions", json={"audio_id": a["id"]})
    tid = r.json()["id"]

    r = client.post(f"/transcriptions/{tid}/running")
    assert r.status_code in (200, 409)

    payload = {"language_detected": "en", "confidence": 0.5, "text_full": "hello", "artifacts": {"srt": "1", "vtt": "1"}}
    r = client.post(f"/transcriptions/{tid}/succeeded", json=payload)
    assert r.status_code in (200, 404)
    if r.status_code == 404:
        r = client.post(f"/transcriptions/{tid}/failed")
        assert r.status_code == 200

    r = client.delete(f"/transcriptions/{tid}")
    assert r.status_code == 200

def _audio(client):
    u = client.post("/users", json={"email": "tedge@example.com", "pwd_hash": "x"}).json()
    p = client.post("/projects", json={"owner_id": u["id"], "name": "T"}).json()
    return client.post("/audio", json={"project_id": p["id"], "s3_uri": "http://files/audio/audio.mp3"}).json()

def test_transcription_create_invalid_audio(client):
    with patch("app.routers.transcriptions.process_transcription", autospec=True):
        r = client.post("/transcriptions", json={"audio_id": "00000000-0000-0000-0000-000000000000"})
        assert r.status_code == 400

def test_transcription_mark_running_twice(client):
    a = _audio(client)
    with patch("app.routers.transcriptions.process_transcription", autospec=True):
        r = client.post("/transcriptions", json={"audio_id": a["id"]})
        tid = r.json()["id"]
    r1 = client.post(f"/transcriptions/{tid}/running")
    r2 = client.post(f"/transcriptions/{tid}/running")
    assert r1.status_code in (200, 409)
    assert r2.status_code == 409

def test_transcription_not_found_ops(client):
    r = client.get("/transcriptions/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404
    r = client.post("/transcriptions/00000000-0000-0000-0000-000000000000/failed")
    assert r.status_code == 404
    r = client.delete("/transcriptions/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404

def test_transcription_invalid_mode(client):
    a = _bootstrap_audio(client)
    with patch("app.routers.transcriptions.process_transcription", autospec=True):
        r = client.post("/transcriptions", json={"audio_id": a["id"], "mode": "nope"})
        assert r.status_code == 400

def test_transcription_failed_then_succeeded_allowed(client):
    a = _bootstrap_audio(client)
    with patch("app.routers.transcriptions.process_transcription", autospec=True):
        r = client.post("/transcriptions", json={"audio_id": a["id"]})
        tid = r.json()["id"]
    r = client.post(f"/transcriptions/{tid}/failed")
    assert r.status_code == 200
    payload = {"language_detected": "en", "confidence": 0.1, "text_full": "x", "artifacts": {"srt": "1", "vtt": "1"}}
    r = client.post(f"/transcriptions/{tid}/succeeded", json=payload)
    assert r.status_code == 200
