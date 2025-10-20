from typing import Optional, List, Dict, Any
from app.db_pool import get_conn

def _rows_to_dicts(cur, rows):
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r)) for r in rows]

def _row_to_dict(cur, row):
    return dict(zip([d[0] for d in cur.description], row)) if row else None

def upsert_subscription(transcription_id: str, user_id: str, channels: str) -> Dict[str, Any]:
    sql = (
        "INSERT INTO notification_subscriptions (transcription_id, user_id, channels) "
        "VALUES (%(tid)s, %(uid)s, %(ch)s) "
        "ON CONFLICT (transcription_id, user_id) DO UPDATE SET channels = EXCLUDED.channels, created_at = NOW() "
        "RETURNING id, transcription_id, user_id, channels, created_at;"
    )
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, {"tid": transcription_id, "uid": user_id, "ch": channels})
        row = cur.fetchone()
        conn.commit()
        return _row_to_dict(cur, row)

def list_subscriptions(transcription_id: str) -> List[Dict[str, Any]]:
    sql = "SELECT * FROM notification_subscriptions WHERE transcription_id = %(tid)s;"
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, {"tid": transcription_id})
        return _rows_to_dicts(cur, cur.fetchall())

def delete_subscription(transcription_id: str, user_id: str) -> Optional[str]:
    sql = "DELETE FROM notification_subscriptions WHERE transcription_id = %(tid)s AND user_id = %(uid)s RETURNING id;"
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, {"tid": transcription_id, "uid": user_id})
        row = cur.fetchone()
        conn.commit()
        return row[0] if row else None
