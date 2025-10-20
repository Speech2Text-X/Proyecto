from typing import Optional, Dict, Any
from app.db_pool import get_conn

def _row_to_dict(cur, row):
    return dict(zip([d[0] for d in cur.description], row)) if row else None

def create_user(email: str, name: Optional[str], pwd_hash: str, role: str = "user") -> Dict[str, Any]:
    sql = (
        "INSERT INTO users (email, name, pwd_hash, role) "
        "VALUES (%(email)s, %(name)s, %(pwd_hash)s, COALESCE(%(role)s, 'user')::role_enum) "
        "RETURNING id, email, name, role, created_at;"
    )
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, {"email": email, "name": name, "pwd_hash": pwd_hash, "role": role})
        row = cur.fetchone()
        conn.commit()
        return _row_to_dict(cur, row)

def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    sql = "SELECT id, email, name, role, created_at FROM users WHERE id = %(id)s;"
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, {"id": user_id})
        return _row_to_dict(cur, cur.fetchone())

def get_user_for_login(email: str) -> Optional[Dict[str, Any]]:
    sql = "SELECT id, email, pwd_hash, role FROM users WHERE email = %(email)s;"
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, {"email": email})
        return _row_to_dict(cur, cur.fetchone())

def update_user(user_id: str, name: Optional[str] = None, role: Optional[str] = None) -> Optional[Dict[str, Any]]:
    sql = (
        "UPDATE users SET name = COALESCE(%(name)s, name), role = COALESCE(%(role)s, role) "
        "WHERE id = %(id)s RETURNING id, email, name, role, created_at;"
    )
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, {"id": user_id, "name": name, "role": role})
        row = cur.fetchone()
        conn.commit()
        return _row_to_dict(cur, row)

def delete_user(user_id: str) -> Optional[str]:
    sql = "DELETE FROM users WHERE id = %(id)s RETURNING id;"
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, {"id": user_id})
        row = cur.fetchone()
        conn.commit()
        return row[0] if row else None
