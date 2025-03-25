
from datetime import timedelta
from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session
from api.models.user import User, UserRole, Role, user_role
from api.dependencies.database import get_db
from api.utils.auth import create_access_token, get_current_active_admin, get_current_user, get_password_hash, verify_password
from config import get_settings
from jose import JWTError, jwt

router = APIRouter()
setting = get_settings()

class UserCreate(BaseModel):
    username: str
    password: str
    role: UserRole = UserRole.USER  # 保留用于向后兼容

class RoleCreate(BaseModel):
    name: str
    description: str
    is_default: bool = False

class RoleResponse(BaseModel):
    id: int
    name: str
    description: str
    is_default: bool

class UserRoleAssign(BaseModel):
    role_ids: List[int]

class UserResponse(BaseModel):
    id: int
    username: str
    role: UserRole  # 保留用于向后兼容
    roles: List[RoleResponse]

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
    
    # 如果是新用户，分配默认角色
    default_role = db.query(Role).filter(Role.is_default == 1).first()
    if default_role:
        db_user.roles.append(default_role)
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return {
        "id": db_user.id,
        "username": db_user.username,
        "role": db_user.role,
        "roles": db_user.roles
    }

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
        data={"sub": user.username,"role":user.role.value}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/users/me", response_model=UserResponse)
async def read_users_me(current_user: Annotated[User, Depends(get_current_user)]):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "role": current_user.role,
        "roles": current_user.roles
    }

@router.get("/users/list", response_model=list[UserResponse])
async def read_all_users(
    current_user: Annotated[User, Depends(get_current_active_admin)],
    db: Session = Depends(get_db)
):
    users = db.query(User).all()
    return [{
        "id": user.id,
        "username": user.username,
        "role": user.role,
        "roles": user.roles
    } for user in users]

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

@router.get("/public-key")
async def get_public_key():
    with open(setting.public_key_path, "r") as key_file:
        public_key = key_file.read()
    return {"public_key": public_key}

# 角色管理API
@router.post("/roles/create", response_model=RoleResponse)
async def create_role(
    role: RoleCreate,
    current_user: Annotated[User, Depends(get_current_active_admin)],
    db: Session = Depends(get_db)
):
    db_role = db.query(Role).filter(Role.name == role.name).first()
    if db_role:
        raise HTTPException(status_code=400, detail="Role already exists")
    
    db_role = Role(
        name=role.name,
        description=role.description,
        is_default=1 if role.is_default else 0
    )
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    return db_role

@router.get("/roles/list", response_model=list[RoleResponse])
async def get_roles(
    current_user: Annotated[User, Depends(get_current_active_admin)],
    db: Session = Depends(get_db)
):
    return db.query(Role).all()

@router.post("/users/{user_id}/roles/assign", response_model=UserResponse)
async def assign_roles_to_user(
    user_id: int,
    roles: UserRoleAssign,
    current_user: Annotated[User, Depends(get_current_active_admin)],
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 清除现有角色
    user.roles = []
    
    # 添加新角色
    for role_id in roles.role_ids:
        role = db.query(Role).filter(Role.id == role_id).first()
        if role:
            user.roles.append(role)
    
    db.commit()
    db.refresh(user)
    return {
        "id": user.id,
        "username": user.username,
        "role": user.role,
        "roles": user.roles
    }

@router.get("/users/{user_id}/roles/list", response_model=list[RoleResponse])
async def get_user_roles(
    user_id: int,
    current_user: Annotated[User, Depends(get_current_active_admin)],
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user.roles
