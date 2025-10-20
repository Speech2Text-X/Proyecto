from fastapi import APIRouter, HTTPException, Query
from typing import List, Any, Dict
from app.schemas import AudioCreate
from app import repo_audio_files

router = APIRouter()

@router.post("")
def create_audio(payload: AudioCreate):
    try:
        return repo_audio_files.create_audio(
            project_id=payload.project_id,
            s3_uri=payload.s3_uri,
            duration_sec=payload.duration_sec,
            sample_rate=payload.sample_rate,
            channels=payload.channels,
            format=payload.format,
            size_bytes=payload.size_bytes,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{audio_id}")
def get_audio(audio_id: str):
    a = repo_audio_files.get_audio(audio_id)
    if not a:
        raise HTTPException(status_code=404, detail="Audio not found")
    return a

@router.get("")
def list_audio(project_id: str, limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)):
    return repo_audio_files.list_audio(project_id, limit, offset)
