from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas, auth
from ..database import get_db
from ..config import settings
import aiohttp

router = APIRouter()

@router.get("/repos", response_model=List[schemas.GitHubRepo])
async def get_github_repos(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.github_token:
        raise HTTPException(
            status_code=400,
            detail="GitHub token not configured"
        )
    
    headers = {
        'Authorization': f'token {current_user.github_token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f'https://api.github.com/users/{current_user.github_username}/repos',
            headers=headers
        ) as response:
            if response.status == 404:
                raise HTTPException(status_code=404, detail="GitHub user not found")
            response.raise_for_status()
            return await response.json()

@router.get("/events", response_model=List[schemas.GitHubEvent])
async def get_github_events(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.github_token:
        raise HTTPException(
            status_code=400,
            detail="GitHub token not configured"
        )
    
    headers = {
        'Authorization': f'token {current_user.github_token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f'https://api.github.com/users/{current_user.github_username}/events',
            headers=headers
        ) as response:
            if response.status == 404:
                raise HTTPException(status_code=404, detail="GitHub user not found")
            response.raise_for_status()
            return await response.json() 