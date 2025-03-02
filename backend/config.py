from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    # 数据库配置
    database_url: str = "mysql+pymysql://root:123456@localhost:3306/data_load"
    
    # JWT配置
    secret_key: str = "your-secret-key"  # 生产环境应使用环境变量
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # 密码加密密钥
    vite_encryption_key: str
    
    # GitHub API配置
    github_api_url: str = "https://api.github.com"
    github_repo_type: str = "all"  # all, owner, member
    github_repo_sort: str = "updated"  # created, updated, pushed, full_name
    github_repo_direction: str = "desc"  # asc, desc
    github_repo_per_page: int = 20
    
    # Toggl配置
    toggl_api_token: str = ""

    vite_encryption_key: str  # 添加此行以允许该字段
    class Config:
        env_file = ".env"
        extra = "allow"  # 允许额外字段

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings() 