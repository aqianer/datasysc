from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime
import models, schemas, auth
from config import settings
from database import get_db
import aiohttp

router = APIRouter()

async def sync_github_repos(user: models.User, db: Session):
    """同步GitHub仓库数据到数据库"""
    if not user.github_token:
        raise HTTPException(
            status_code=400,
            detail="GitHub token not configured"
        )
    
    headers = {
        'Authorization': f'token {user.github_token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    params = {
        'type': settings.github_repo_type,
        'sort': settings.github_repo_sort,
        'direction': settings.github_repo_direction,
        'per_page': settings.github_repo_per_page
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f'https://api.github.com/users/{user.github_username}/repos',
            headers=headers,
            params=params
        ) as response:
            if response.status == 404:
                raise HTTPException(status_code=404, detail="GitHub user not found")
            response.raise_for_status()
            repos = await response.json()
            
            # 更新数据库
            for repo in repos:
                db_repo = db.query(models.GitHubRepo).filter(
                    models.GitHubRepo.user_id == user.id,
                    models.GitHubRepo.github_id == repo['id']
                ).first()
                
                repo_data = {
                    'user_id': user.id,
                    'github_id': repo['id'],
                    'repo_name': repo['name'],
                    'fork_flag': repo['fork'],
                    'events_url': repo['events_url'],
                    'description': repo['description'],
                    'created_at': datetime.strptime(repo['created_at'], '%Y-%m-%dT%H:%M:%SZ'),
                    'updated_at': datetime.strptime(repo['updated_at'], '%Y-%m-%dT%H:%M:%SZ'),
                    'pushed_at': datetime.strptime(repo['pushed_at'], '%Y-%m-%dT%H:%M:%SZ'),
                    'status': 1
                }
                
                if db_repo:
                    for key, value in repo_data.items():
                        setattr(db_repo, key, value)
                else:
                    db_repo = models.GitHubRepo(**repo_data)
                    db.add(db_repo)
            
            db.commit()

@router.get("/repos", response_model=List[schemas.GitHubRepo])
async def get_github_repos(
    page: int = Query(1, gt=0),
    per_page: int = Query(5, gt=0, le=20),
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """获取GitHub仓库列表，支持分页"""
    # 先同步最新数据
    await sync_github_repos(current_user, db)
    
    # 从数据库获取分页数据
    total = db.query(models.GitHubRepo).filter(
        models.GitHubRepo.user_id == current_user.id,
        models.GitHubRepo.status == 1
    ).count()
    
    repos = db.query(models.GitHubRepo).filter(
        models.GitHubRepo.user_id == current_user.id,
        models.GitHubRepo.status == 1
    ).order_by(
        desc(models.GitHubRepo.updated_at)
    ).offset(
        (page - 1) * per_page
    ).limit(per_page).all()
    
    return {
        'items': repos,
        'total': total,
        'page': page,
        'per_page': per_page
    }

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