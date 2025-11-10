from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from typing import List
from app.schemas import TranscriptionCreate, TranscriptionSuccess
from app import repo_transcriptions, repo_segments
from app.services.transcribe import process_transcription

router = APIRouter()

@router.post("")
def create_transcription(payload: TranscriptionCreate, background_tasks: BackgroundTasks):
    try:
        t = repo_transcriptions.create_transcription(
            audio_id=payload.audio_id,
            mode=payload.mode,
            language_hint=payload.language_hint,
            model_name=payload.model_name,
            temperature=payload.temperature,
            beam_size=payload.beam_size,
        )
        # Encolar procesamiento en background
        background_tasks.add_task(process_transcription, t["id"])
        return t
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{tid}")
def get_transcription(tid: str):
    t = repo_transcriptions.get_transcription(tid)
    if not t:
        raise HTTPException(status_code=404, detail="Transcription not found")
    return t

@router.get("")
def list_transcriptions(audio_id: str, limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)):
    return repo_transcriptions.list_transcriptions_by_audio(audio_id, limit, offset)

@router.post("/{tid}/running")
def mark_running(tid: str):
    t = repo_transcriptions.mark_running(tid)
    if not t:
        raise HTTPException(status_code=409, detail="Cannot move to running from current state")
    return t

@router.post("/{tid}/succeeded")
def mark_succeeded(tid: str, payload: TranscriptionSuccess):
    t = repo_transcriptions.mark_succeeded(
        tid, payload.language_detected, payload.confidence, payload.text_full, payload.artifacts
    )
    if not t:
        raise HTTPException(status_code=404, detail="Transcription not found")
    return t

@router.post("/{tid}/failed")
def mark_failed(tid: str):
    t = repo_transcriptions.mark_failed(tid)
    if not t:
        raise HTTPException(status_code=404, detail="Transcription not found")
    return t

@router.delete("/{tid}")
def delete_transcription(tid: str):
    tid2 = repo_transcriptions.hard_delete(tid)
    if not tid2:
        raise HTTPException(status_code=404, detail="Transcription not found")
    return {"deleted": tid2}
