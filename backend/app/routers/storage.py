from fastapi import APIRouter
from pydantic import BaseModel
from uuid import uuid4
from app.aws import presign_put, presign_get, AWS_S3_BUCKET

router = APIRouter()

class UploadIn(BaseModel):
    user_id: str
    ext: str = "mp3"
    content_type: str = "audio/mpeg"

@router.post("/upload-url")
def upload_url(body: UploadIn):
    key = f"audio/{body.user_id}/{uuid4()}.{body.ext}"
    url = presign_put(key, body.content_type)
    s3_uri = f"s3://{AWS_S3_BUCKET}/{key}"  # esto es lo que guardarás en DB
    return {"key": key, "url": url, "s3_uri": s3_uri}

@router.get("/file-url")
def file_url(key: str, content_type: str | None = None):
    return {"url": presign_get(key, response_content_type=content_type)}
