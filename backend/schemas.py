from pydantic import BaseModel, EmailStr, HttpUrl, Json
from typing import Optional, List, Dict, Any
from datetime import datetime

# 基础模型
class BaseResponse(BaseModel):
    class Config:
        from_attributes = True

# 用户相关模型
class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str
    nickname: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

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
    token_type: str = "bearer"
    expires_at: datetime

# 计划相关模型
class PlanBase(BaseModel):
    plan_name: str
    toggl_project_id: int
    repo_id: int
    daily_plan_duration: float
    tag_list: Json
    project_list: Json
    deadline: datetime

class PlanCreate(PlanBase):
    pass

class PlanUpdate(BaseModel):
    plan_name: Optional[str] = None
    toggl_project_id: Optional[int] = None
    repo_id: Optional[int] = None
    daily_plan_duration: Optional[float] = None
    tag_list: Optional[Json] = None
    project_list: Optional[Json] = None
    deadline: Optional[datetime] = None
    plan_status: Optional[int] = None

class PlanResponse(PlanBase, BaseResponse):
    id: int
    user_id: int
    plan_status: int
    created_time: datetime
    update_time: datetime

# Toggl相关模型
class TogglProject(BaseModel):
    id: int
    name: str
    workspace_id: int
    active: bool
    created_at: datetime

class TogglTag(BaseModel):
    id: int
    name: str
    workspace_id: int

# GitHub相关模型
class GitHubRepo(BaseModel):
    id: int
    name: str
    full_name: str
    html_url: HttpUrl
    description: Optional[str] = None
    private: bool
    created_at: datetime
    updated_at: datetime

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
    plan_status: Json
    heat_level: int
    total_duration: int
    is_core_completed: bool

class DailyStatusResponse(DailyStatus, BaseResponse):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime 