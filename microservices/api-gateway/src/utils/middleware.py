# app/utils/middleware.py
import re
from typing import Dict, List
from fastapi import Request
from fastapi.responses import JSONResponse
import httpx
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware
from async_lru import alru_cache
from config import get_settings
# 需要过滤的headers列表
SENSITIVE_HEADERS = {
    'host', 'content-length', 
    'connection', 'keep-alive'
}

setting=get_settings()
class RoutePermission(BaseModel):
    # 路径名称或标识
    path: str
    # 权限要求：可以是一个角色名，也可以是特定的权限标签（如 "public", "admin", "user"）
    required_permission: List[str]  # 例如 ["admin"]

# 服务权限模型，包含各个路由的权限要求
class ServicePermissions(BaseModel):
    service_name: str
    permissions: Dict[str, RoutePermission]

# 缓存服务权限配置
@alru_cache(maxsize=32)
async def get_service_permissions(service_url: str):
    try:
        # 向服务请求权限配置
        permissions_url = f"{service_url}/permissions"
        async with httpx.AsyncClient() as client:
            response = await client.get(permissions_url)
            if response.status_code == 200:
                return response.json()
            else:
                return {}
    except httpx.RequestError:
        return {}
    
class GatewayMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, registry, balancer):
        super().__init__(app)
        self.registry = registry
        self.balancer = balancer
    def get_service_url_from_registry(self, service_name: str):
        """
        从服务注册表中获取服务实例并返回服务的 URL。
        如果没有可用实例，返回 503 错误的 JSONResponse。
        """
        instances = self.registry.get_healthy_instances(service_name)
        if not instances:
            return None  # 返回 None 表示没有可用实例

        # 获取第一个健康实例的 URL
        target = instances[0]
        return f"http://{target.host}:{target.port}"
    
    async def dispatch(self, request: Request, call_next):
        # 1. 跳过内部接口（如健康检查）
        if request.url.path.startswith("/_internal"):
            return await call_next(request)
        # 路径不对直接返回
        path_parts = request.url.path.split('/')
        if len(path_parts) < 2:
            return JSONResponse(
                status_code=404,
                content={"message": "Invalid path format"}
            )
            
        # 2. 获取请求路径的权限要求
        service_name = path_parts[1] if len(path_parts) > 1 else None
        
        # 3. 获取该服务的实例，解析出服务的权限配置
        service_url = self.get_service_url_from_registry(service_name)
        if not service_url:
            return JSONResponse(
                status_code=503,
                content={"message": f"No available instances for {service_name}"}
            )
        
        # 4. 获取服务的权限配置
        permissions = await get_service_permissions(service_url)
        
        # 获取当前请求的权限要求
        service_permissions:list = permissions.get("permissions", {})
        current_path = '/' + '/'.join(path_parts[2:])
        def path_to_regex(pattern: str) -> str:
            """将路径模式转换为正则表达式"""
            return re.sub(r'\{([^}]+)\}', r'(?P<\1>[^/]+)', pattern) + '$'

        route_permission = None
        for perm in service_permissions:
            # 将权限配置中的路径转换为正则表达式
            pattern = re.compile(path_to_regex(perm['path']))
            if pattern.match(current_path):
                route_permission = perm
                break


        # 5. 如果路径不需要权限控制（即 route_permission 为 None 或者 required_permission 为public）
        if route_permission is None or route_permission['required_permission']==['public']:
            # 不需要权限认证，直接转发请求
            return await self._forward_request(request, call_next)
        
        # 4. 如果路径需要权限，检查是否有有效的 JWT Token
        auth_header = request.headers.get("Authorization")
        if not auth_header or "Bearer " not in auth_header:
            return JSONResponse(
                status_code=401,
                content={"message": "Missing or invalid Authorization header"}
            )
        token = auth_header.split("Bearer ")[-1]

        # 5. 调用用户管理服务验证令牌
        management_url = self.get_service_url_from_registry("user_management")
        if not management_url:
            return JSONResponse(
                status_code=503,
                content={"message": f"No available instances for {service_name}"}
            )
        
        verify_url = f"{management_url}/verify-token"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    verify_url,
                    json={"token": token},
                    headers={"Content-Type": "application/json"}
                )
                if response.status_code != 200:
                    return JSONResponse(
                        status_code=401,
                        content={"message": "Invalid or expired token"}
                    )
                user_info = response.json()  # 包含用户ID、角色等信息
        except httpx.RequestError:
            return JSONResponse(
                status_code=503,
                content={"message": "User management service unavailable"}
            )

        # 8. 校验用户角色是否符合权限要求
        if route_permission and user_info["role"] not in route_permission['required_permission']:
            return JSONResponse(
                status_code=403,
                content={"message": f"Access to {request.url.path} requires one of the following roles: {', '.join(route_permission['required_permission'])}"}
            )

        #转发请求
        return await self._forward_request(request, call_next, user_info)
            
    async def _forward_request(self, request: Request, call_next, user_info=None):
        """
        转发请求给服务，并携带用户信息（如果需要）
        """
        # 如果需要携带用户信息，添加 X-User-ID 和 X-User-Role
        new_headers = {
            key: value for key, value in request.headers.items()
            if key.lower() not in SENSITIVE_HEADERS
        }
        if user_info:
            new_headers["X-User-ID"] = str(user_info["id"])
            new_headers["X-User-Role"] = user_info["role"]
        
        # 获取目标服务实例
        path_parts = request.url.path.split('/')
        service_name = path_parts[1] if len(path_parts) > 1 else None
        instances = self.registry.get_healthy_instances(service_name)
        if not instances:
            return JSONResponse(
                status_code=503,
                content={"message": f"No available instances for {service_name}"}
            )
        service_id_header = request.headers.get("X-Service-ID",None)
        # 选择实例并构造新的 URL
        target = self.balancer.select_instance(instances, service_id_header)
        if not target and service_id_header:
            return JSONResponse(
                status_code=404,
                content={"message": f"Service instance with ID {service_id_header} not found"}
            )
        new_path = '/' + '/'.join(path_parts[2:]) if len(path_parts) > 2 else '/'
        
        # 构建新的 headers
        new_headers["host"] = f"{target.host}:{target.port}"
        new_headers["x-forwarded-for"] = request.client.host if request.client else "unknown"
        new_headers["x-forwarded-host"] = str(request.url.hostname)
        new_headers["x-forwarded-proto"] = request.url.scheme
        
        # 转发请求
        try:
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method=request.method,
                    url=f"http://{target.host}:{target.port}{new_path}",
                    headers=new_headers,
                    params=request.query_params,
                    content=await request.body()
                )
                return JSONResponse(
                    content=response.json(),
                    status_code=response.status_code,
                    headers=dict(response.headers)
                )
        except httpx.ConnectError:
            # 标记实例为不健康
            target.is_healthy = False
            return JSONResponse(
                status_code=503,
                content={"message": "Service connection failed"}
             )
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"message": f"Service error: {str(e)}"}
            )