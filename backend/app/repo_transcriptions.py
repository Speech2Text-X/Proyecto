from typing import Optional, List, Dict, Any
from app.db_pool import get_conn
import json

def _rows_to_dicts(cur, rows):
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r)) for r in rows]

def _row_to_dict(cur, row):
    return dict(zip([d[0] for d in cur.description], row)) if row else None

def create_transcription(audio_id: str, mode: str = "batch", language_hint: str = None,
                         model_name: str = None, temperature: float = None, beam_size: int = None) -> Dict[str, Any]:
    sql = (
        "INSERT INTO transcriptions (audio_id, mode, status, language_hint, model_name, temperature, beam_size, started_at) "
        "VALUES (%(audio_id)s, COALESCE(%(mode)s, 'batch')::mode_enum, 'queued', %(language_hint)s, "
        "%(model_name)s, %(temperature)s, %(beam_size)s, NOW()) "
        "RETURNING id, audio_id, mode, status, started_at;"
    )
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, {
            "audio_id": audio_id, "mode": mode, "language_hint": language_hint,
            "model_name": model_name, "temperature": temperature, "beam_size": beam_size
        })
        row = cur.fetchone()
        conn.commit()
        return _row_to_dict(cur, row)

def get_transcription(tid: str) -> Optional[Dict[str, Any]]:
    sql = "SELECT * FROM transcriptions WHERE id = %(id)s;"
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, {"id": tid})
        return _row_to_dict(cur, cur.fetchone())

def list_transcriptions_by_audio(audio_id: str, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
    sql = (
        "SELECT id, audio_id, mode, status, language_detected, model_name, started_at, finished_at "
        "FROM transcriptions WHERE audio_id = %(audio_id)s "
        "ORDER BY started_at DESC LIMIT %(limit)s OFFSET %(offset)s;"
    )
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, {"audio_id": audio_id, "limit": limit, "offset": offset})
        return _rows_to_dicts(cur, cur.fetchall())

def mark_running(tid: str) -> Optional[Dict[str, Any]]:
    sql = "UPDATE transcriptions SET status='running' WHERE id=%(id)s AND status='queued' RETURNING id, status;"
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, {"id": tid})
        row = cur.fetchone()
        conn.commit()
        return _row_to_dict(cur, row)

def mark_succeeded(tid: str, language_detected: str, confidence: float, text_full: str, artifacts: dict) -> Optional[Dict[str, Any]]:
    sql = (
        "UPDATE transcriptions SET status='succeeded', language_detected=%(language_detected)s, confidence=%(confidence)s, "
        "text_full=%(text_full)s, artifacts=%(artifacts)s::jsonb, finished_at=NOW() "
        "WHERE id=%(id)s RETURNING id, status, language_detected, finished_at;"
    )
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, {
            "id": tid, "language_detected": language_detected, "confidence": confidence,
            "text_full": text_full, "artifacts": json.dumps(artifacts or {})
        })
        row = cur.fetchone()
        conn.commit()
        return _row_to_dict(cur, row)

def mark_failed(tid: str) -> Optional[Dict[str, Any]]:
    sql = "UPDATE transcriptions SET status='failed', finished_at=NOW() WHERE id=%(id)s RETURNING id, status, finished_at;"
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, {"id": tid})
        row = cur.fetchone()
        conn.commit()
        return _row_to_dict(cur, row)

def hard_delete(tid: str) -> Optional[str]:
    sql = "DELETE FROM transcriptions WHERE id=%(id)s RETURNING id;"
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, {"id": tid})
        row = cur.fetchone()
        conn.commit()
        return row[0] if row else None
