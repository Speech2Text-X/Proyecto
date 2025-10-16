from typing import Optional, List, Any
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from uuid import UUID

# ------- Users -------
class UserCreate(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    pwd_hash: str
    role: Optional[str] = "user"

class UserOut(BaseModel):
    id: UUID
    email: EmailStr
    name: Optional[str] = None
    role: str
    created_at: datetime

# ------- Projects -------
class ProjectCreate(BaseModel):
    owner_id: UUID
    name: str

class ProjectUpdate(BaseModel):
    name: Optional[str] = None

class ProjectOut(BaseModel):
    id: UUID
    owner_id: UUID
    name: str
    created_at: datetime

# ------- Audio Files -------
class AudioCreate(BaseModel):
    project_id: UUID
    s3_uri: str
    duration_sec: Optional[int] = None
    sample_rate: Optional[int] = None
    channels: Optional[int] = None
    format: Optional[str] = None
    size_bytes: Optional[int] = None

# ------- Transcriptions -------
class TranscriptionCreate(BaseModel):
    audio_id: UUID
    mode: Optional[str] = "batch"
    language_hint: Optional[str] = None
    model_name: Optional[str] = None
    temperature: Optional[float] = None
    beam_size: Optional[int] = None

class TranscriptionSuccess(BaseModel):
    language_detected: str
    confidence: Optional[float] = None
    text_full: str
    artifacts: Any = Field(default_factory=dict)

# ------- Segments -------
class SegmentCreate(BaseModel):
    start_ms: int
    end_ms: int
    text: str
    speaker_label: Optional[str] = None
    confidence: Optional[float] = None

# ------- Shares -------
class ShareCreate(BaseModel):
    transcription_id: UUID
    kind: Optional[str] = "private"
    token: str
    can_edit: Optional[bool] = False
    expires_at: Optional[datetime] = None
    created_by: Optional[UUID] = None

class ShareUpdate(BaseModel):
    kind: Optional[str] = None
    can_edit: Optional[bool] = None
    expires_at: Optional[datetime] = None

# ------- Notifications -------
class NotificationCreate(BaseModel):
    transcription_id: UUID
    user_id: Optional[UUID] = None
    type: str
    target: str
    status: Optional[str] = "pending"
    payload: Optional[Any] = None

class UpdateNotificationStatus(BaseModel):
    status: str
    payload: Optional[Any] = None
