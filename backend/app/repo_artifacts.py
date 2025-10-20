from typing import List, Dict, Any, Optional
from app.db_pool import get_conn

def _rows_to_dicts(cur, rows):
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r)) for r in rows]

def _row_to_dict(cur, row):
    return dict(zip([d[0] for d in cur.description], row)) if row else None

def upsert_artifact(transcription_id: str, kind: str, s3_uri: str) -> Dict[str, Any]:
    sql = (
        "INSERT INTO transcription_artifacts (transcription_id, kind, s3_uri) "
        "VALUES (%(tid)s, %(kind)s, %(uri)s) "
        "ON CONFLICT (transcription_id, kind) DO UPDATE SET s3_uri = EXCLUDED.s3_uri, created_at = NOW() "
        "RETURNING id, transcription_id, kind, s3_uri, created_at;"
    )
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, {"tid": transcription_id, "kind": kind, "uri": s3_uri})
        row = cur.fetchone()
        conn.commit()
        return _row_to_dict(cur, row)

def list_artifacts(transcription_id: str) -> List[Dict[str, Any]]:
    sql = "SELECT * FROM transcription_artifacts WHERE transcription_id = %(tid)s ORDER BY created_at DESC;"
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, {"tid": transcription_id})
        return _rows_to_dicts(cur, cur.fetchall())

def delete_artifact(transcription_id: str, kind: str) -> Optional[str]:
    sql = "DELETE FROM transcription_artifacts WHERE transcription_id = %(tid)s AND kind = %(kind)s RETURNING id;"
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, {"tid": transcription_id, "kind": kind})
        row = cur.fetchone()
        conn.commit()
        return row[0] if row else None
