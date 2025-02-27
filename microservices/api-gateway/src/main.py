# app/main.py
import socket
from fastapi import FastAPI
from contextlib import asynccontextmanager

import uvicorn
from services.registry import ServiceInstance
from utils.middleware import GatewayMiddleware
from endpoints import api
from config import get_settings
from core import registry, balancer


setting = get_settings()
hostname=socket.gethostname()
# 注册服务到Consul
instance = ServiceInstance(
        service_name="api-gateway",
        instance_id=f"api-gateway-{hostname}",
        host=socket.gethostbyname(hostname),
        port=setting.port,
        health_check_url=f"http://{socket.gethostbyname(hostname)}:{setting.port}/_internal/health"
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

@app.get("/_internal/health")
def gateway_health():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=setting.port)
