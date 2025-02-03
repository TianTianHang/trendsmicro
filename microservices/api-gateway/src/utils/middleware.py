# app/utils/middleware.py
from fastapi import Request
from fastapi.responses import JSONResponse
import httpx
from starlette.middleware.base import BaseHTTPMiddleware

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
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method=request.method,
                    url=f"http://{target.host}:{target.port}{new_path}",
                    headers=dict(request.headers),
                    params=request.query_params,
                    content=await request.body()
                )
                return JSONResponse(
                    content=response.json(),
                    status_code=response.status_code,
                    headers=dict(response.headers)
                )
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"message": f"Service error: {str(e)}"}
            )