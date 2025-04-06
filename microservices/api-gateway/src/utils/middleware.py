# app/utils/middleware.py
from typing import Dict, List
from fastapi import Request
from fastapi.responses import JSONResponse
import httpx
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware
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
        
        # 4. 调用权限服务进行token和权限校验
        current_path = '/' + '/'.join(path_parts[2:])
        auth_header = request.headers.get("Authorization")
       
        headers = {"Content-Type": "application/json", "Authorization": auth_header if auth_header else ""}
        
        # 先调用user_management服务检查并刷新token
        user_service_url = self.get_service_url_from_registry("user_management")
        if user_service_url and auth_header and auth_header.startswith("Bearer "):
            try:
                async with httpx.AsyncClient() as client:
                    refresh_response = await client.post(
                        f"{user_service_url}/refresh-token",
                        headers={"Authorization": auth_header}
                    )
                    if refresh_response.status_code == 200:
                        
                        refresh_data = refresh_response.json()
                        if refresh_data.get("refreshed"):
                            # 更新请求头中的token
                            headers["Authorization"] = f"Bearer {refresh_data.get('new_token')}"
                        new_token = refresh_data.get("new_token",None)
                    
            except httpx.RequestError:
                pass
                
        # 然后调用权限服务验证权限
        permission_service_url = self.get_service_url_from_registry("permission")
        if not permission_service_url:
            return JSONResponse(
                status_code=503,
                content={"message": "Permission service unavailable"}
            )
            
        verify_permission_url = f"{permission_service_url}/verify-permission"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    verify_permission_url,
                    json={"service_name": service_name, "path": current_path},
                    headers=headers
                )
              
                user_info = response.json().get("user_info",None)
                if response.status_code != 200:
                    return JSONResponse(
                        status_code=response.status_code,
                        content={"message": response.json().get("detail", "Permission denied")}
                    )
                
               
        except httpx.RequestError:
            return JSONResponse(
                status_code=503,
                content={"message": "Permission service unavailable"}
            )
        
        #转发请求
        return await self._forward_request(request, call_next,user_info,new_token if "new_token" in locals() else None)
            
    async def _forward_request(self, request: Request, call_next, user_info=None,new_token=None):
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
            #print(f"http://{target.host}:{target.port}{new_path}")
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method=request.method,
                    url=f"http://{target.host}:{target.port}{new_path}",
                    headers=new_headers,
                    params=request.query_params,
                    content=await request.body()
                )
                 # 如果有新token，添加到响应头
                if new_token:
                    response.headers["X-New-Token"] = new_token
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
