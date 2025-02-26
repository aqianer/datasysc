from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # 数据库配置
    database_url: str = "mysql+pymysql://root:123456@localhost:3306/data_load"
    
    # JWT配置
    secret_key: str = "your-secret-key"  # 生产环境应使用环境变量
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # GitHub配置
    github_token: str = ""
    
    # Toggl配置
    toggl_api_token: str = ""
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings() 