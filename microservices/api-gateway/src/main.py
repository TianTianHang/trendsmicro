# app/main.py
import socket
from fastapi import FastAPI, Request
from contextlib import asynccontextmanager

from fastapi.responses import JSONResponse
import uvicorn
from services.registry import ServiceInstance
from utils.middleware import GatewayMiddleware
from endpoints import api
from config import get_settings
from core import registry, balancer
from fastapi.middleware.cors import CORSMiddleware

settings= get_settings()
hostname=socket.gethostname()
# 注册服务到Consul
instance = ServiceInstance(
        service_name="api-gateway",
        instance_id=f"api-gateway-{hostname}",
        host=socket.gethostbyname(hostname),
        port=settings.port,
        health_check_url=f"http://{socket.gethostbyname(hostname)}:{settings.port}/_internal/health"
    )

@asynccontextmanager
async def lifespan(app: FastAPI):
   
    
    registry.register(instance)
    yield
    # 注销服务
    registry.deregister(instance.service_name, instance.instance_id)
    

app = FastAPI(lifespan=lifespan)
app.include_router(api.router)
app.add_middleware(
    GatewayMiddleware,
    registry=registry,
    balancer=balancer
)
origins = [
    "https://page.918113.top",  # 根据实际情况调整为您的前端应用的源
    # 您可以根据需要添加更多的源
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/_internal/health")
def gateway_health():
    return {"status": "healthy"}
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
        # 全局异常处理
        return JSONResponse(
            status_code=500,
            content={
                "message": "Internal Server Error",
                "detail": str(exc) if settings.debug else "An error occurred"
            }
        )
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=settings.port)
