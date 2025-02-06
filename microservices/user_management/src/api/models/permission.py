# 定义路由权限模型
from typing import List
from pydantic import BaseModel


class RoutePermission(BaseModel):
    path: str
    required_permission: List[str]  # 权限要求，例如 ["admin", "user"]

# 定义服务权限模型
class ServicePermissionsResponse(BaseModel):
    service_name: str
    permissions: List[RoutePermission]