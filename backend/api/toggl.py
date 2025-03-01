import requests
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List
import models, schemas, auth
from database import get_db
import json

from logger import get_logger

logger = get_logger(__name__)

router = APIRouter()

@router.get("/projects", response_model=List[schemas.TogglProject])
def get_toggl_projects(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """从数据库获取最新的Toggl项目列表"""
    # 获取最新的toggl数据记录
    latest_toggl_data = db.query(models.TogglData).filter(
        models.TogglData.user_id == current_user.id
    ).order_by(
        desc(models.TogglData.update_time)
    ).first()
    
    if not latest_toggl_data:
        raise HTTPException(
            status_code=404,
            detail="No Toggl data found"
        )
    
    try:
        # 解析project_list JSON数据
        project_list = json.loads(latest_toggl_data.project_list)
        if not isinstance(project_list, dict) or 'projects' not in project_list:
            raise ValueError("Invalid project list format")
        
        # 返回项目列表
        return project_list['projects']
    except (json.JSONDecodeError, ValueError) as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse Toggl project data: {str(e)}"
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