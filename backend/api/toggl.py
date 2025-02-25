from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas, auth
from ..database import get_db
from ..config import settings
import requests

router = APIRouter()

@router.get("/projects", response_model=List[schemas.TogglProject])
def get_toggl_projects(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.toggl_api_token:
        raise HTTPException(
            status_code=400,
            detail="Toggl API token not configured"
        )
    
    auth_string = f"{current_user.toggl_api_token}:api_token"
    headers = {
        'content-type': 'application/json',
        'Authorization': f'Basic {auth_string}'
    }
    
    response = requests.get(
        'https://api.track.toggl.com/api/v9/me/projects',
        headers=headers
    )
    response.raise_for_status()
    
    return response.json()

@router.get("/tags", response_model=List[schemas.TogglTag])
def get_toggl_tags(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.toggl_api_token:
        raise HTTPException(
            status_code=400,
            detail="Toggl API token not configured"
        )
    
    auth_string = f"{current_user.toggl_api_token}:api_token"
    headers = {
        'content-type': 'application/json',
        'Authorization': f'Basic {auth_string}'
    }
    
    response = requests.get(
        'https://api.track.toggl.com/api/v9/me/tags',
        headers=headers
    )
    response.raise_for_status()
    
    return response.json() 