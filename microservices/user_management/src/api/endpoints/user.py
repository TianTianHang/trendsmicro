
from datetime import datetime, timedelta
from typing import Annotated, List,Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from api.models.user import User, UserRole, Role, user_role
from api.dependencies.database import get_db
from api.utils.auth import create_access_token, decode_token, get_current_active_admin, get_current_user, get_password_hash, verify_password
from config import get_settings
from jose import JWTError, jwt

router = APIRouter()
setting = get_settings()

class UserCreate(BaseModel):
    username: str
    password: str
    email: EmailStr
    full_name: str = None
    phone: str = None
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
    email: EmailStr
    full_name: str = None
    phone: str = None
    is_active: int
    created_at: str
    last_login: Optional[str] = None
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
        email=user.email,
        full_name=user.full_name,
        phone=user.phone,
        role=user.role,
        is_active=1,  # 默认激活
        last_login=None  # 新用户还未登录
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
        "email": db_user.email,
        "full_name": db_user.full_name,
        "phone": db_user.phone,
        "is_active": db_user.is_active,
        "created_at": db_user.created_at.strftime("%Y-%m-%d %H:%M:%S") if db_user.created_at else None,
        "last_login": db_user.last_login.strftime("%Y-%m-%d %H:%M:%S") if db_user.last_login else None,
        "role": db_user.role,
        "roles": db_user.roles
    }

@router.post("/token", response_model=Token)
def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: Session = Depends(get_db)):
    if form_data.username == "guest":
        guestRole = Role(id=0, name="guest", description="guest", is_default=False)
        user = User(
            id=0,
            username="guest",
            email="guest@example.com",
            full_name="Guest User",
            phone=None,
            is_active=1,
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            last_login=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            role="guest",
            roles=[guestRole]
        )
        access_token_expires = timedelta(minutes=60*24)
        access_token = create_access_token(
            data={"sub": user.username, "roles": [r.name for r in user.roles]}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}
    
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )
    
    # 检查用户是否处于激活状态
    if not user.is_active==1:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="账户已被禁用，请联系管理员",
        )
    
    # 更新最后登录时间
    user.last_login = datetime.now()
    db.commit()
    
    access_token_expires = timedelta(minutes=setting.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username,"roles":[r.name for r in user.roles]}, 
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/users/me", response_model=UserResponse)
async def read_users_me(current_user: Annotated[User, Depends(get_current_user)]):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "phone": current_user.phone,
        "is_active": current_user.is_active,
        "created_at": current_user.created_at.strftime("%Y-%m-%d %H:%M:%S") if current_user.created_at else None,
        "last_login": current_user.last_login.strftime("%Y-%m-%d %H:%M:%S") if current_user.last_login else None,
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
        "email": user.email,
        "full_name": user.full_name,
        "phone": user.phone,
        "is_active": user.is_active,
        "created_at": user.created_at.strftime("%Y-%m-%d %H:%M:%S") if user.created_at else None,
        "last_login": user.last_login.strftime("%Y-%m-%d %H:%M:%S") if user.last_login else None,
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
        "email": user.email,
        "full_name": user.full_name,
        "phone": user.phone,
        "is_active": user.is_active,
        "created_at": user.created_at.strftime("%Y-%m-%d %H:%M:%S") if user.created_at else None,
        "last_login": user.last_login.strftime("%Y-%m-%d %H:%M:%S") if user.last_login else None,
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

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

@router.post("/users/change_password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    # 验证旧密码
    if not verify_password(request.old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Old password is incorrect"
        )
    
    # 更新为新密码
    current_user.hashed_password = get_password_hash(request.new_password)
    db.commit()
    
    return {"message": "Password updated successfully"}

@router.post("/refresh-token")
async def refresh_token(
    request: Request,
    db: Session = Depends(get_db)
):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    token = auth_header.split(" ")[1]
    try:
        # 解码但不验证过期时间
        payload = decode_token(token)
        username: str = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token")
        if username=="guest": 
            guestRole=Role(id=0,name="guest",description="guest",is_default=False)
            user = User(id = 0,
                username = "guest",
                role = "guest",
                roles=[guestRole])
        else:
            # 查询用户
            user = db.query(User).filter(User.username == username).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        result = {"refreshed":False}
        
        # 检查token有效期
        exp = payload.get("exp")
      
        if exp and (exp - datetime.now().timestamp()) < 300:  # 剩余5分钟
            # 生成新token
            access_token_expires = timedelta(minutes=setting.access_token_expire_minutes)
            new_token = create_access_token(
                data={"sub": user.username, "roles": [r.name for r in user.roles]},
                expires_delta=access_token_expires
            )
            result["new_token"] = new_token
            result["refreshed"] = True
        return result
        
    except JWTError:
        raise HTTPException(status_code=401, detail="Token validation failed")
