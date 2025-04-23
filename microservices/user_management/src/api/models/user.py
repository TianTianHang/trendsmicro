from sqlalchemy import Column, Integer, String, Enum, ForeignKey, Table,DateTime
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from api.dependencies.database import Base
from sqlalchemy.sql import func
# 保留原有UserRole枚举用于向后兼容
class UserRole(PyEnum):
    ADMIN = "admin"
    USER = "user"
    GUEST ="guest"

# 角色表
class Role(Base):
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True)
    description = Column(String(200))
    is_default = Column(Integer, default=0)  # 0-非默认 1-默认角色

# 用户-角色关联表
user_role = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("role_id", Integer, ForeignKey("roles.id"), primary_key=True)
)

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    hashed_password = Column(String(100))
    role = Column(Enum(UserRole), default=UserRole.USER)  # 保留原有字段用于向后兼容
    
    # 新增基本信息字段
    email = Column(String(100), unique=True, index=True)
    full_name = Column(String(100))
    phone = Column(String(20))
    is_active = Column(Integer, default=1)  # 1-活跃 0-禁用
    created_at = Column(DateTime,default=func.now())  # 创建时间
    last_login = Column(DateTime)  # 最后登录时间
    
    # 用户角色关系
    roles = relationship(
        "Role",
        secondary=user_role,
        backref="users"
    )