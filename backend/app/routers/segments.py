from fastapi import APIRouter, HTTPException, Query
from typing import List
from app.schemas import SegmentCreate
from app import repo_segments

router = APIRouter()

@router.post("/{tid}")
def create_segment(tid: str, payload: SegmentCreate):
    seg_id = repo_segments.insert_segment(
        transcription_id=tid,
        start_ms=payload.start_ms,
        end_ms=payload.end_ms,
        text=payload.text,
        speaker_label=payload.speaker_label,
        confidence=payload.confidence,
    )
    return {"id": seg_id}

@router.get("/{tid}")
def list_segments(tid: str, limit: int = Query(1000, ge=1, le=5000), offset: int = Query(0, ge=0)):
    return repo_segments.list_segments(tid, limit, offset)

@router.delete("/{tid}")
def delete_segments(tid: str):
    n = repo_segments.delete_segments_by_transcription(tid)
    return {"deleted": n}
