from typing import Optional, Dict, Any
from app.db_pool import get_conn

VALID_KINDS = {"private", "public"}

def _row_to_dict(cur, row):
    return dict(zip([d[0] for d in cur.description], row)) if row else None

def create_share(transcription_id: str, token: str, kind: str = "private",
                 can_edit: bool = False, expires_at: str = None, created_by: str = None) -> Dict[str, Any]:
    sql = (
        "INSERT INTO shares (transcription_id, kind, token, can_edit, expires_at, created_by) "
        "VALUES (%(tid)s, COALESCE(%(kind)s, 'private')::share_kind_enum, %(token)s, "
        "COALESCE(%(edit)s,false), %(exp)s, %(by)s) "
        "RETURNING id, transcription_id, kind, token, can_edit, expires_at, created_at;"
    )
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, {
            "tid": transcription_id,
            "kind": kind,
            "token": token,
            "edit": can_edit,
            "exp": expires_at,
            "by": created_by
        })
        row = cur.fetchone()
        conn.commit()
        return _row_to_dict(cur, row)

def resolve_share(token: str, grace_seconds: int = 300) -> Optional[Dict[str, Any]]:
    """
    Resuelve un share por token, incluyendo un margen de 'grace_seconds'
    para evitar que un share recién creado aparezca como expirado.
    """
    sql = (
        "SELECT s.id, s.transcription_id, s.kind, s.token, s.can_edit, s.expires_at, "
        "s.created_by, s.created_at, t.status "
        "FROM shares s "
        "JOIN transcriptions t ON t.id = s.transcription_id "
        "WHERE s.token = %(token)s "
        "AND (s.expires_at IS NULL OR (s.expires_at + (%(grace)s || ' seconds')::interval) > NOW());"
    )
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, {"token": token, "grace": grace_seconds})
        return _row_to_dict(cur, cur.fetchone())

def cleanup_expired() -> int:
    sql = "DELETE FROM shares WHERE expires_at IS NOT NULL AND expires_at <= NOW() RETURNING id;"
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql)
        rows = cur.fetchall()
        conn.commit()
        return len(rows)


def update_share(share_id: str, kind: str = None, can_edit: bool = None, expires_at: str = None):
    if kind is not None and kind not in VALID_KINDS:
        raise ValueError(f"Invalid kind: {kind}. Must be one of {VALID_KINDS}")

    sql = (
        "UPDATE shares SET kind = COALESCE(%(kind)s, kind)::share_kind_enum, "
        "can_edit = COALESCE(%(edit)s, can_edit), "
        "expires_at = COALESCE(%(exp)s, expires_at) "
        "WHERE id = %(id)s RETURNING id, kind, can_edit, expires_at;"
    )
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, {"id": share_id, "kind": kind, "edit": can_edit, "exp": expires_at})
        row = cur.fetchone()
        conn.commit()
        return _row_to_dict(cur, row)

def delete_share(share_id: str) -> Optional[str]:
    sql = "DELETE FROM shares WHERE id = %(id)s RETURNING id;"
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, {"id": share_id})
        row = cur.fetchone()
        conn.commit()
        return row[0] if row else None
