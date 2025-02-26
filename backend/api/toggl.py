from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import models, schemas, auth
from database import get_db
from config import settings
import requests
from logger import get_logger

router = APIRouter()
logger = get_logger(__name__)

@router.get("/projects", response_model=List[schemas.TogglProject])
def get_toggl_projects(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    logger.info(f"Fetching Toggl projects for user: {current_user.username}")
    
    if not current_user.toggl_api_token:
        logger.error(f"Toggl API token not configured for user: {current_user.username}")
        raise HTTPException(
            status_code=400,
            detail="Toggl API token not configured"
        )

    auth_string = f"{current_user.toggl_api_token}:api_token"
    headers = {
        'content-type': 'application/json',
        'Authorization': f'Basic {auth_string}'
    }

    try:
        response = requests.get(
            'https://api.track.toggl.com/api/v9/me/projects',
            headers=headers
        )
        response.raise_for_status()
        logger.info(f"Successfully fetched {len(response.json())} Toggl projects")
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching Toggl projects: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching Toggl projects: {str(e)}"
        )

@router.get("/tags", response_model=List[schemas.TogglTag])
def get_toggl_tags(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    logger.info(f"Fetching Toggl tags for user: {current_user.username}")
    
    if not current_user.toggl_api_token:
        logger.error(f"Toggl API token not configured for user: {current_user.username}")
        raise HTTPException(
            status_code=400,
            detail="Toggl API token not configured"
        )

    auth_string = f"{current_user.toggl_api_token}:api_token"
    headers = {
        'content-type': 'application/json',
        'Authorization': f'Basic {auth_string}'
    }

    try:
        response = requests.get(
            'https://api.track.toggl.com/api/v9/me/tags',
            headers=headers
        )
        response.raise_for_status()
        logger.info(f"Successfully fetched {len(response.json())} Toggl tags")
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching Toggl tags: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching Toggl tags: {str(e)}"
        )