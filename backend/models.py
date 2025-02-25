from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON, ForeignKey, TIMESTAMP, Float, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    nickname = Column(String(50))
    avatar_url = Column(String(255))
    
    # 第三方平台信息
    github_username = Column(String(50))
    github_token = Column(String(255))
    toggl_email = Column(String(100))
    toggl_api_token = Column(String(255))
    toggl_workspace_id = Column(Integer)
    
    # 状态信息
    status = Column(Integer, default=1, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    last_login_time = Column(DateTime)
    last_login_ip = Column(String(45))
    
    # 时间戳
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    # 其他信息
    phone = Column(String(20))
    timezone = Column(String(50), default='Asia/Shanghai')
    language = Column(String(10), default='zh-CN')
    notification_prefs = Column(JSON)
    
    # 关系
    plans = relationship("PersonalPlan", back_populates="user")
    daily_status = relationship("DailyStatus", back_populates="user")

class PersonalPlan(Base):
    __tablename__ = "personal_plans"
    
    id = Column(Integer, primary_key=True)
    plan_id = Column(Integer, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    plan_name = Column(String(30), nullable=False)
    toggl_project_id = Column(Integer, nullable=False)
    repo_id = Column(Integer, nullable=False)
    daily_plan_duration = Column(Float, nullable=False)
    tag_list = Column(JSON, nullable=False)
    project_list = Column(JSON, nullable=False)
    create_time = Column(DateTime, nullable=False, server_default=func.now())
    update_time = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    deadline = Column(Date, nullable=False)
    plan_status = Column(Integer, nullable=False)
    plan_type = Column(Integer, nullable=False)
    
    # 关系
    user = relationship("User", back_populates="plans")

class DailyStatus(Base):
    __tablename__ = "daily_status"
    
    record_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    record_date = Column(Date, nullable=False)
    plan_status = Column(JSON, nullable=False)
    heat_level = Column(Integer, nullable=False)
    total_duration = Column(Integer)
    is_core_completed = Column(Boolean, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    # 关系
    user = relationship("User", back_populates="daily_status")

class UserLoginHistory(Base):
    __tablename__ = "user_login_history"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    login_time = Column(DateTime, nullable=False, server_default=func.now())
    login_ip = Column(String(45), nullable=False)
    login_device = Column(String(255), nullable=False)
    login_status = Column(Integer, nullable=False)
    login_type = Column(String(20), nullable=False, default='password')

class UserToken(Base):
    __tablename__ = "user_tokens"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    token_type = Column(String(20), nullable=False)
    token_value = Column(String(255), nullable=False, unique=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now()) 