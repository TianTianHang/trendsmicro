from datetime import datetime, timedelta
from typing import Annotated
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, Request,status
from jose import JWTError, jwt
from api.models.user import User, UserRole
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer

from config import get_settings
from api.dependencies.database import get_db
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")
setting = get_settings()
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, setting.secret_key, algorithm=setting.algorithm)
    return encoded_jwt

async def get_current_user(request: Request,token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    # 从请求头部获取用户ID和角色
    user_id = request.headers.get("X-User-ID")
    user_role = request.headers.get("X-User-Role")

    if not user_id or not user_role:
        raise credentials_exception

    # 查询数据库中的用户信息
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_admin(
    current_user: Annotated[User, Depends(get_current_user)]
):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=400, detail="Insufficient permissions")
    return current_user
