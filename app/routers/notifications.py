from fastapi import APIRouter, HTTPException, Query
from typing import List
from app.schemas import NotificationCreate, UpdateNotificationStatus
from app import repo_notifications

router = APIRouter()

@router.post("")
def create_notification(payload: NotificationCreate):
    try:
        return repo_notifications.create_notification(
            transcription_id=payload.transcription_id,
            user_id=payload.user_id,
            type_=payload.type,
            target=payload.target,
            status=payload.status,
            payload=payload.payload,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"DB error: {str(e)}")

@router.get("")
def list_notifications(transcription_id: str, limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)):
    return repo_notifications.list_notifications(transcription_id, limit, offset)

@router.post("/{nid}/status")
def update_status(nid: str, payload: UpdateNotificationStatus):
    n = repo_notifications.update_notification_status(nid, payload.status, payload.payload)
    if not n:
        raise HTTPException(status_code=404, detail="Notification not found")
    return n

@router.delete("/{nid}")
def delete_notification(nid: str):
    did = repo_notifications.delete_notification(nid)
    if not did:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"deleted": did}
