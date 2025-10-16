from typing import Optional, List, Dict, Any
from app.db_pool import get_conn
import json
from fastapi import HTTPException

# --- ENUMS ---
VALID_STATUS = {"pending", "sent", "failed"}  # Debe coincidir con tu enum en PostgreSQL

# --- Helpers ---
def _rows_to_dicts(cur, rows):
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r)) for r in rows]

def _row_to_dict(cur, row):
    return dict(zip([d[0] for d in cur.description], row)) if row else None

# --- CRUD ---
def create_notification(
    transcription_id: str,
    type_: str,
    target: str,
    user_id: Optional[str] = None,
    status: str = "pending",
    payload: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    # Validar enum
    if status not in VALID_STATUS:
        raise ValueError(f"Invalid status '{status}', must be one of {VALID_STATUS}")

    sql = (
        "INSERT INTO notifications (transcription_id, user_id, type, target, status, payload) "
        "VALUES (%(tid)s, %(uid)s, %(type)s, %(target)s, COALESCE(%(status)s,'pending')::notification_status_enum, %(payload)s::jsonb) "
        "RETURNING id, transcription_id, type, target, status, payload, created_at;"
    )

    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, {
            "tid": transcription_id,
            "uid": user_id,
            "type": type_,
            "target": target,
            "status": status,
            "payload": json.dumps(payload or {})
        })
        row = cur.fetchone()
        conn.commit()
        return _row_to_dict(cur, row)

def list_notifications(transcription_id: str, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
    sql = (
        "SELECT id, transcription_id, type, target, status, payload, created_at "
        "FROM notifications WHERE transcription_id = %(tid)s "
        "ORDER BY created_at DESC LIMIT %(limit)s OFFSET %(offset)s;"
    )
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, {"tid": transcription_id, "limit": limit, "offset": offset})
        return _rows_to_dicts(cur, cur.fetchall())

def update_notification_status(nid: str, status: str, payload: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    if status not in VALID_STATUS:
        raise ValueError(f"Invalid status '{status}', must be one of {VALID_STATUS}")

    sql = (
        "UPDATE notifications "
        "SET status = %(status)s::notification_status_enum, "
        "payload = COALESCE(%(payload)s::jsonb, payload) "
        "WHERE id = %(id)s "
        "RETURNING id, status, payload, created_at;"
    )
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, {
            "id": nid,
            "status": status,
            "payload": json.dumps(payload) if payload else None
        })
        row = cur.fetchone()
        conn.commit()
        return _row_to_dict(cur, row)

def delete_notification(nid: str) -> Optional[str]:
    sql = "DELETE FROM notifications WHERE id = %(id)s RETURNING id;"
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, {"id": nid})
        row = cur.fetchone()
        conn.commit()
        return row[0] if row else None
