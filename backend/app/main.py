from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import users, projects, audio, transcriptions, segments, shares, notifications, health, storage

app = FastAPI(title="Speech2Text X API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(projects.router, prefix="/projects", tags=["projects"])
app.include_router(audio.router, prefix="/audio", tags=["audio"])
app.include_router(transcriptions.router, prefix="/transcriptions", tags=["transcriptions"])
app.include_router(segments.router, prefix="/segments", tags=["segments"])
app.include_router(shares.router, prefix="/shares", tags=["shares"])
app.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
app.include_router(storage.router, prefix="/storage", tags=["storage"])