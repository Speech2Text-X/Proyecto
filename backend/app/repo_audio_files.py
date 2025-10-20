from typing import Optional, List, Dict, Any
from app.db_pool import get_conn

def _rows_to_dicts(cur, rows):
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r)) for r in rows]

def _row_to_dict(cur, row):
    return dict(zip([d[0] for d in cur.description], row)) if row else None

def create_audio(project_id: str, s3_uri: str, duration_sec: int = None,
                 sample_rate: int = None, channels: int = None,
                 format: str = None, size_bytes: int = None) -> Dict[str, Any]:
    sql = (
        "INSERT INTO audio_files (project_id, s3_uri, duration_sec, sample_rate, channels, format, size_bytes) "
        "VALUES (%(project_id)s, %(s3_uri)s, %(duration_sec)s, %(sample_rate)s, %(channels)s, %(format)s, %(size_bytes)s) "
        "RETURNING id, project_id, s3_uri, duration_sec, sample_rate, channels, format, size_bytes, created_at;"
    )
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, { "project_id": project_id, "s3_uri": s3_uri, "duration_sec": duration_sec,
                           "sample_rate": sample_rate, "channels": channels, "format": format, "size_bytes": size_bytes })
        row = cur.fetchone()
        conn.commit()
        return _row_to_dict(cur, row)

def get_audio(audio_id: str) -> Optional[Dict[str, Any]]:
    sql = "SELECT * FROM audio_files WHERE id = %(id)s;"
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, {"id": audio_id})
        return _row_to_dict(cur, cur.fetchone())

def list_audio(project_id: str, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
    sql = (
        "SELECT * FROM audio_files WHERE project_id = %(project_id)s "
        "ORDER BY created_at DESC LIMIT %(limit)s OFFSET %(offset)s;"
    )
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, {"project_id": project_id, "limit": limit, "offset": offset})
        return _rows_to_dicts(cur, cur.fetchall())

def update_audio(audio_id: str, **fields) -> Optional[Dict[str, Any]]:
    sql = (
        "UPDATE audio_files "
        "SET duration_sec = COALESCE(%(duration_sec)s, duration_sec), "
        "    sample_rate  = COALESCE(%(sample_rate)s,  sample_rate), "
        "    channels     = COALESCE(%(channels)s,     channels), "
        "    format       = COALESCE(%(format)s,       format) "
        "WHERE id = %(id)s RETURNING *;"
    )
    params = {"id": audio_id, **fields}
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        row = cur.fetchone()
        conn.commit()
        return _row_to_dict(cur, row)

def delete_audio(audio_id: str) -> Optional[str]:
    sql = "DELETE FROM audio_files WHERE id = %(id)s RETURNING id;"
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, {"id": audio_id})
        row = cur.fetchone()
        conn.commit()
        return row[0] if row else None
