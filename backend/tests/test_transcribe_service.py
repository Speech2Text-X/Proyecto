from types import SimpleNamespace
from unittest.mock import patch

from app import repo_transcriptions, repo_audio_files, repo_projects, repo_users
from app.db_pool import get_conn
from app.services.transcribe import process_transcription


def _bootstrap_data():
    u = repo_users.create_user("svc@example.com", "Svc", "x", "user")
    p = repo_projects.create_project(u["id"], "SvcProj")
    a = repo_audio_files.create_audio(project_id=p["id"], s3_uri="http://files/audio/audio.mp3")
    t = repo_transcriptions.create_transcription(audio_id=a["id"])
    return t["id"]


class _FakeWhisperModel:
    def transcribe(self, audio_path, language=None, temperature=None, beam_size=None):
        class _Seg:
            def __init__(self, start, end, text):
                self.start = start
                self.end = end
                self.text = text

        segments = iter(
            [
                _Seg(0.0, 0.8, "Hello"),
                _Seg(0.8, 1.6, "world"),
            ]
        )
        info = SimpleNamespace(language=language or "en", language_probability=0.9)
        return segments, info


def test_process_transcription_success(monkeypatch):
    tid = _bootstrap_data()

    monkeypatch.setenv("WHISPER_MODEL", "tiny")

    def _fake_download(uri: str) -> str:
        return __file__

    with patch("app.services.transcribe._load_model", return_value=_FakeWhisperModel()):
        with patch("app.services.transcribe.download_audio_to_temp", side_effect=_fake_download):
            process_transcription(tid)

    t = repo_transcriptions.get_transcription(tid)
    assert t and t["status"] == "succeeded"
    assert t["text_full"]
    assert t["language_detected"]
    assert "-->" in t["artifacts"]["srt"]
    assert t["artifacts"]["vtt"].startswith("WEBVTT")

    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM segments WHERE transcription_id = %(tid)s", {"tid": tid})
        n = cur.fetchone()[0]
        assert n >= 2

def _bootstrap_bad_audio():
    u = repo_users.create_user("fail@example.com", None, "x", "user")
    p = repo_projects.create_project(u["id"], "Fail")
    a = repo_audio_files.create_audio(project_id=p["id"], s3_uri="http://files/audio/does-not-exist.wav")
    t = repo_transcriptions.create_transcription(audio_id=a["id"])
    return t["id"]

def test_process_transcription_failure():
    tid = _bootstrap_bad_audio()
    try:
        process_transcription(tid)
    except Exception:
        pass
    t = repo_transcriptions.get_transcription(tid)
    assert t and t["status"] == "failed"

def test_process_transcription_http_404(monkeypatch):
    tid = _bootstrap_data()
    import requests
    def _raise_http_error(uri: str):
        raise requests.HTTPError("404")
    with patch("app.services.transcribe.download_audio_to_temp", side_effect=_raise_http_error):
        try:
            process_transcription(tid)
        except Exception:
            pass
    t = repo_transcriptions.get_transcription(tid)
    assert t and t["status"] == "failed"

def test_disable_whisper_env_produces_empty_artifacts(monkeypatch):
    tid = _bootstrap_data()
    monkeypatch.setenv("S2X_DISABLE_WHISPER", "1")
    process_transcription(tid)
    t = repo_transcriptions.get_transcription(tid)
    assert t and t["status"] == "succeeded"
    assert t["artifacts"]["num_segments"] == 0
    assert t["artifacts"]["srt"] == ""
    assert t["artifacts"]["vtt"] == ""
    monkeypatch.delenv("S2X_DISABLE_WHISPER", raising=False)

def test_model_env_overrides(monkeypatch):
    from app.services import transcribe as tr
    class _DummyModel:
        def __init__(self, name, device="cpu", compute_type=None):
            self.name = name
            self.device = device
            self.compute_type = compute_type
    monkeypatch.setenv("WHISPER_MODEL", "tiny")
    monkeypatch.setenv("WHISPER_COMPUTE_TYPE", "float32")
    with patch.object(tr, "WhisperModel", _DummyModel):
        m = tr._load_model()
    assert m.name == "tiny"
    assert m.device == "cpu"
    assert m.compute_type == "float32"

def test_build_srt_vtt_time_boundaries():
    from app.services.transcribe import build_srt, build_vtt
    segs = [
        {"start_ms": 0, "end_ms": 999, "text": "A"},
        {"start_ms": 999, "end_ms": 1001, "text": "B"},
        {"start_ms": 3599000, "end_ms": 3600000, "text": "C"},
    ]
    srt = build_srt(segs)
    vtt = build_vtt(segs)
    assert "00:00:00,000" in srt
    assert "00:00:00.000" in vtt
    assert "WEBVTT" in vtt

def test_segments_bulk_and_pagination_order():
    from app import repo_segments, repo_transcriptions, repo_projects, repo_users, repo_audio_files
    u = repo_users.create_user("bulk@example.com", None, "x", "user")
    p = repo_projects.create_project(u["id"], "Bulk")
    a = repo_audio_files.create_audio(p["id"], "http://files/audio/audio.mp3")
    t = repo_transcriptions.create_transcription(a["id"])
    segs = [{"start_ms": i, "end_ms": i + 1, "text": "x"} for i in range(0, 2000)]
    n = repo_segments.bulk_insert_segments(t["id"], segs)
    assert n == 2000
    from app import repo_segments as rs
    page1 = rs.list_segments(t["id"], limit=1000, offset=0)
    page2 = rs.list_segments(t["id"], limit=1000, offset=1000)
    assert len(page1) == 1000 and len(page2) == 1000
    assert page1[0]["start_ms"] == 0
    assert page2[0]["start_ms"] == 1000

def test_artifacts_uniqueness_on_upsert():
    from app import repo_artifacts, repo_transcriptions, repo_projects, repo_users, repo_audio_files
    u = repo_users.create_user("art@example.com", None, "x", "user")
    p = repo_projects.create_project(u["id"], "Art")
    a = repo_audio_files.create_audio(p["id"], "http://files/audio/audio.mp3")
    t = repo_transcriptions.create_transcription(a["id"])
    repo_artifacts.upsert_artifact(t["id"], "srt", "s3://dummy/s1.srt")
    repo_artifacts.upsert_artifact(t["id"], "srt", "s3://dummy/s2.srt")
    arts = repo_artifacts.list_artifacts(t["id"])
    kinds = [x["kind"] for x in arts]
    assert kinds.count("srt") == 1
