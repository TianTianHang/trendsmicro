from datetime import timedelta
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException,status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session
from api.models.user import User, UserRole
from api.dependencies.database import get_db
from microservices.user_management.src.api.utils.auth import create_access_token, get_current_active_admin, get_current_user, get_password_hash, verify_password
from config import get_settings
from jose import JWTError, jwt


router = APIRouter(prefix="/user")
setting = get_settings()

class UserCreate(BaseModel):
    username: str
    password: str
    role: UserRole = UserRole.USER

class UserResponse(BaseModel):
    id: int
    username: str
    role: UserRole

class Token(BaseModel):
    access_token: str
    token_type: str
    
@router.post("/register", response_model=UserResponse)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        hashed_password=hashed_password,
        role=user.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.post("/token", response_model=Token)
def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    
    access_token_expires = timedelta(minutes=setting.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/users/me", response_model=UserResponse)
async def read_users_me(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user

@router.get("/users", response_model=list[UserResponse])
async def read_all_users(
    current_user: Annotated[User, Depends(get_current_active_admin)],
    db: Session = Depends(get_db)
):
    return db.query(User).all()

class TokenValidationRequest(BaseModel):
    token: str

@router.post("/verify-token")
async def verify_token(req: TokenValidationRequest, db: Session = Depends(get_db)):
    try:
        # 验证JWT令牌
        payload = jwt.decode(req.token, setting.secret_key, algorithms=[setting.algorithm])
        username: str = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # 查询用户信息
        user = db.query(User).filter(User.username == username).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        return {
            "id": user.id,
            "username": user.username,
            "role": user.role.value  # 返回枚举值字符串
        }
    except JWTError:
        raise HTTPException(status_code=401, detail="Token validation failed")