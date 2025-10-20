from fastapi import APIRouter, HTTPException, Query
from typing import List
from app.schemas import ProjectCreate, ProjectUpdate, ProjectOut
from app import repo_projects

router = APIRouter()

@router.post("", response_model=ProjectOut)
def create_project(payload: ProjectCreate):
    try:
        return repo_projects.create_project(payload.owner_id, payload.name)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{project_id}", response_model=ProjectOut)
def get_project(project_id: str):
    p = repo_projects.get_project(project_id)
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    return p

@router.get("", response_model=List[ProjectOut])
def list_projects(owner_id: str, limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)):
    return repo_projects.list_projects(owner_id, limit, offset)

@router.patch("/{project_id}", response_model=ProjectOut)
def update_project(project_id: str, owner_id: str, payload: ProjectUpdate):
    p = repo_projects.update_project(project_id, owner_id, payload.name)
    if not p:
        raise HTTPException(status_code=404, detail="Not found or not owner")
    return p

@router.delete("/{project_id}")
def delete_project(project_id: str, owner_id: str):
    pid = repo_projects.delete_project(project_id, owner_id)
    if not pid:
        raise HTTPException(status_code=404, detail="Not found or not owner")
    return {"deleted": pid}
