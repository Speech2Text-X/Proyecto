from typing import Optional, List, Dict, Any
from app.db_pool import get_conn

def _rows_to_dicts(cur, rows):
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r)) for r in rows]

def _row_to_dict(cur, row):
    return dict(zip([d[0] for d in cur.description], row)) if row else None

def create_project(owner_id: str, name: str) -> Dict[str, Any]:
    sql = (
        "INSERT INTO projects (owner_id, name) VALUES (%(owner_id)s, %(name)s) "
        "RETURNING id, owner_id, name, created_at;"
    )
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, {"owner_id": owner_id, "name": name})
        row = cur.fetchone()
        conn.commit()
        return _row_to_dict(cur, row)

def get_project(project_id: str) -> Optional[Dict[str, Any]]:
    sql = "SELECT id, owner_id, name, created_at FROM projects WHERE id = %(id)s;"
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, {"id": project_id})
        return _row_to_dict(cur, cur.fetchone())

def list_projects(owner_id: str, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
    sql = (
        "SELECT id, owner_id, name, created_at FROM projects "
        "WHERE owner_id = %(owner_id)s ORDER BY created_at DESC "
        "LIMIT %(limit)s OFFSET %(offset)s;"
    )
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, {"owner_id": owner_id, "limit": limit, "offset": offset})
        return _rows_to_dicts(cur, cur.fetchall())

def update_project(project_id: str, owner_id: str, name: Optional[str]) -> Optional[Dict[str, Any]]:
    sql = (
        "UPDATE projects SET name = COALESCE(%(name)s, name) "
        "WHERE id = %(id)s AND owner_id = %(owner_id)s "
        "RETURNING id, owner_id, name, created_at;"
    )
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, {"id": project_id, "owner_id": owner_id, "name": name})
        row = cur.fetchone()
        conn.commit()
        return _row_to_dict(cur, row)

def delete_project(project_id: str, owner_id: str) -> Optional[str]:
    sql = "DELETE FROM projects WHERE id = %(id)s AND owner_id = %(owner_id)s RETURNING id;"
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, {"id": project_id, "owner_id": owner_id})
        row = cur.fetchone()
        conn.commit()
        return row[0] if row else None
