def test_health_ok(client):
    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body.get("status") in {"ok", "error"}
    if body.get("status") == "ok":
        assert body.get("db") == 1

