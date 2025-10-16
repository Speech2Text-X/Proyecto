from typing import Optional, List, Dict, Any, Iterable
from app.db_pool import get_conn

def _rows_to_dicts(cur, rows):
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r)) for r in rows]

def insert_segment(transcription_id: str, start_ms: int, end_ms: int, text: str,
                   speaker_label: str = None, confidence: float = None) -> str:
    sql = (
        "INSERT INTO segments (transcription_id, start_ms, end_ms, speaker_label, text, confidence) "
        "VALUES (%(tid)s, %(start)s, %(end)s, %(spk)s, %(txt)s, %(conf)s) RETURNING id;"
    )
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, {"tid": transcription_id, "start": start_ms, "end": end_ms,
                          "spk": speaker_label, "txt": text, "conf": confidence})
        seg_id = cur.fetchone()[0]
        conn.commit()
        return seg_id

def bulk_insert_segments(transcription_id: str, segments: Iterable[Dict[str, Any]]) -> int:
    sql = (
        "INSERT INTO segments (transcription_id, start_ms, end_ms, speaker_label, text, confidence) "
        "VALUES (%(tid)s, %(start)s, %(end)s, %(spk)s, %(txt)s, %(conf)s)"
    )
    count = 0
    with get_conn() as conn, conn.cursor() as cur:
        for s in segments:
            cur.execute(sql, {
                "tid": transcription_id,
                "start": s["start_ms"], "end": s["end_ms"], "spk": s.get("speaker_label"),
                "txt": s["text"], "conf": s.get("confidence")
            })
            count += 1
        conn.commit()
    return count

def list_segments(transcription_id: str, limit: int = 1000, offset: int = 0) -> List[Dict[str, Any]]:
    sql = (
        "SELECT id, start_ms, end_ms, speaker_label, text, confidence FROM segments "
        "WHERE transcription_id = %(tid)s ORDER BY start_ms ASC LIMIT %(limit)s OFFSET %(offset)s;"
    )
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, {"tid": transcription_id, "limit": limit, "offset": offset})
        return _rows_to_dicts(cur, cur.fetchall())

def delete_segments_by_transcription(transcription_id: str) -> int:
    sql = "DELETE FROM segments WHERE transcription_id = %(tid)s RETURNING id;"
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, {"tid": transcription_id})
        rows = cur.fetchall()
        conn.commit()
        return len(rows)
