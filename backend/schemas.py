from pydantic import BaseModel, EmailStr, HttpUrl, Json
from typing import Optional, List, Dict, Any
from datetime import datetime, date

# 基础模型
class BaseResponse(BaseModel):
    class Config:
        from_attributes = True

# 用户相关模型
class UserBase(BaseModel):
    username: str
    email: EmailStr
    nickname: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class User(UserBase):
    id: int
    is_admin: bool
    status: int
    last_login_time: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        orm_mode = True

class UserUpdate(BaseModel):
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None
    github_username: Optional[str] = None
    toggl_email: Optional[str] = None
    github_token: Optional[str] = None
    toggl_api_token: Optional[str] = None

class UserResponse(UserBase, BaseResponse):
    id: int
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None
    is_admin: bool
    created_at: datetime
    github_username: Optional[str] = None
    toggl_email: Optional[str] = None

# Token相关模型
class Token(BaseModel):
    access_token: str
    token_type: str
    expires_at: datetime

# 计划相关模型
class PlanBase(BaseModel):
    plan_name: str
    toggl_project_id: int
    repo_id: int
    daily_plan_duration: float
    deadline: datetime

class PlanCreate(PlanBase):
    pass

class PlanUpdate(PlanBase):
    plan_status: Optional[int] = None
    plan_type: Optional[int] = None

class PlanResponse(PlanBase):
    id: int
    user_id: int
    create_time: datetime
    update_time: datetime
    plan_status: int
    plan_type: int
    
    class Config:
        orm_mode = True

# Toggl相关模型
class TogglProject(BaseModel):
    id: int
    name: str
    workspace_id: Optional[int] = None
    
    class Config:
        orm_mode = True

class TogglTag(BaseModel):
    id: int
    name: str
    workspace_id: int

# GitHub相关模型
class GitHubRepo(BaseModel):
    id: int
    github_id: int
    repo_name: str
    fork_flag: bool
    events_url: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    pushed_at: datetime
    
    class Config:
        orm_mode = True

class GitHubRepoList(BaseModel):
    items: List[GitHubRepo]
    total: int
    page: int
    per_page: int

class GitHubEvent(BaseModel):
    id: str
    type: str
    actor: Dict[str, Any]
    repo: Dict[str, Any]
    payload: Dict[str, Any]
    created_at: datetime

# 统计相关模型
class DailyStatus(BaseModel):
    record_date: datetime
    plan_status: Dict[str, Dict[str, Any]]
    heat_level: int

class DailyStatusResponse(DailyStatus, BaseResponse):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime 