from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import models
import schemas
import auth
from auth import decrypt_password
from database import engine, get_db
from api import users, plans, github, toggl, stats
from logger import get_logger

logger = get_logger(__name__)

app = FastAPI(title="DataSync API")

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vue开发服务器地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建数据库表
models.Base.metadata.create_all(bind=engine)
logger.info("Database tables created successfully")

# 注册路由
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(plans.router, prefix="/api/plans", tags=["plans"])
app.include_router(github.router, prefix="/api/github", tags=["github"])
app.include_router(toggl.router, prefix="/api/toggl", tags=["toggl"])
app.include_router(stats.router, prefix="/api/stats", tags=["stats"])
logger.info("All routes registered successfully")


# 认证路由
@app.post("/api/token", response_model=schemas.Token)
async def login(form_data: schemas.UserLogin, db: Session = Depends(get_db)):
    logger.info("userinfo successfully")

    user = auth.authenticate_user(db, form_data.username, decrypt_password(form_data.password))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 更新最后登录时间
    user.last_login_time = datetime.now()
    db.commit()

    access_token_expires = timedelta(minutes=30)
    access_token = auth.create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_at": datetime.utcnow() + access_token_expires
    }
