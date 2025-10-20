from fastapi import APIRouter, HTTPException
from app.schemas import ShareCreate, ShareUpdate
from app import repo_shares

router = APIRouter()

@router.post("")
def create_share(payload: ShareCreate):
    try:
        return repo_shares.create_share(
            transcription_id=payload.transcription_id,
            token=payload.token,
            kind=payload.kind,
            can_edit=payload.can_edit,
            expires_at=payload.expires_at,
            created_by=payload.created_by,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/resolve/{token}")
def resolve_share(token: str):
    s = repo_shares.resolve_share(token, grace_seconds=60)
    if not s:
        raise HTTPException(status_code=404, detail="Not found or expired")
    return s

@router.post("/cleanup")
def cleanup():
    n = repo_shares.cleanup_expired()
    return {"deleted": n}

@router.patch("/{share_id}")
def update_share_endpoint(share_id: str, payload: ShareUpdate):
    try:
        s = repo_shares.update_share(share_id, payload.kind, payload.can_edit, payload.expires_at)
        if not s:
            raise HTTPException(status_code=404, detail="Share not found")
        return s
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{share_id}")
def delete_share(share_id: str):
    sid = repo_shares.delete_share(share_id)
    if not sid:
        raise HTTPException(status_code=404, detail="Share not found")
    return {"deleted": sid}
