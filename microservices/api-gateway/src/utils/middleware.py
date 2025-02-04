# app/utils/middleware.py
from fastapi import Request
from fastapi.responses import JSONResponse
import httpx
from starlette.middleware.base import BaseHTTPMiddleware
# 需要过滤的headers列表
SENSITIVE_HEADERS = {
    'host', 'content-length', 
    'connection', 'keep-alive'
}

class GatewayMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, registry, balancer):
        super().__init__(app)
        self.registry = registry
        self.balancer = balancer

    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/_internal"):
            return await call_next(request)
        
        path_parts = request.url.path.split('/')
        if len(path_parts) < 2:
            return JSONResponse(
                status_code=404,
                content={"message": "Invalid path format"}
            )

        service_name = path_parts[1]
        instances = self.registry.get_healthy_instances(service_name)
        if not instances:
            return JSONResponse(
                status_code=503,
                content={"message": f"No available instances for {service_name}"}
            )

        target = self.balancer.select_instance(instances)
        new_path = '/' + '/'.join(path_parts[2:]) if len(path_parts) > 2 else '/'
        # 构建新的headers
        new_headers = {
            key: value for key, value in request.headers.items()
            if key.lower() not in SENSITIVE_HEADERS
        }
        new_headers["host"] = f"{target.host}:{target.port}"
        new_headers["x-forwarded-for"] = request.client.host if request.client else "unknown"
        new_headers["x-forwarded-host"] = str(request.url.hostname)
        new_headers["x-forwarded-proto"] = request.url.scheme
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
            