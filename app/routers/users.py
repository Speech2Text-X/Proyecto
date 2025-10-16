from fastapi import APIRouter, HTTPException
from app.schemas import UserCreate, UserOut
from app import repo_users

router = APIRouter()

@router.post("", response_model=UserOut)
def create_user(payload: UserCreate):
    try:
        u = repo_users.create_user(payload.email, payload.name, payload.pwd_hash, payload.role or "user")
        return u
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: str):
    u = repo_users.get_user_by_id(user_id)
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    return u
