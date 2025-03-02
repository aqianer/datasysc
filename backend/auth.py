from datetime import datetime, timedelta
from typing import Optional, Any, Coroutine
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing_extensions import Type

from database import get_db
from models import User
from config import settings
from Cryptodome.Cipher import AES
from Cryptodome.Util.Padding import unpad
import base64

from logger import get_logger

logger = get_logger(__name__)

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def decrypt_password(encrypted_password: str) -> str:
    """解密前端加密的密码"""
    try:
        # 解码Base64密钥
        key = base64.b64decode(settings.vite_encryption_key)
        
        # 解码Base64密文
        combined = base64.b64decode(encrypted_password)
        
        # 前16字节是IV，后面的是加密数据
        iv = combined[:16]
        ciphertext = combined[16:]
        
        # 创建解密器
        cipher = AES.new(key, AES.MODE_CBC, iv)
        
        # 解密并去除填充
        decrypted = unpad(cipher.decrypt(ciphertext), AES.block_size)
        
        return decrypted.decode('utf-8')
    except Exception as e:
        logger.error(f"Password decryption failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid encrypted password"
        )

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """获取密码哈希"""
    return pwd_context.hash(password)

def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """验证用户"""
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password):
        return None
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Type[User]:
    """获取当前用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        
        user = db.query(User).filter(User.username == username).first()
        if user is None:
            raise credentials_exception
        
        if user.status != 1:  # 1表示正常状态
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is disabled"
            )
        
        return user
        
    except JWTError:
        raise credentials_exception

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """获取当前活跃用户"""
    if current_user.status != 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user

async def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """获取当前管理员用户"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough privileges"
        )
    return current_user 