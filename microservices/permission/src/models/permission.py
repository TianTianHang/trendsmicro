from typing import List
from pydantic import BaseModel
from sqlalchemy import Column, String,DateTime

from dependencies.database import Base
from sqlalchemy.sql import func

class RoutePermission(BaseModel):
    path: str
    required_permission: List[str]  # 权限要求，例如 ["admin", "user"]

class ServicePermissionsResponse(BaseModel):
    service_name: str
    permissions: List[RoutePermission]

class Permission(Base):
    __tablename__ = 'permissions'
    service_name = Column(String, primary_key=True)
    path = Column(String, primary_key=True, index=True)
    required_permission = Column(String)  # 存储为逗号分隔的字符串
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __init__(self,service_name, path, required_permission):
        self.service_name= service_name
        self.path = path
        self.required_permission = required_permission

    def to_dict(self):
        return {
            "path": self.path,
            "required_permission": self.required_permission.split(',')
        }
