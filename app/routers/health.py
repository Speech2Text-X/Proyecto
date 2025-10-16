from fastapi import APIRouter
from app.db_pool import get_conn

router = APIRouter()

@router.get("")
def ok():
    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("select 1")
            one = cur.fetchone()[0]
        return {"status": "ok", "db": one}
    except Exception as e:
        return {"status": "error", "error": str(e)}
