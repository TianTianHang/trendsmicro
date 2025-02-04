# app/main.py
from fastapi import FastAPI
from contextlib import asynccontextmanager
import asyncio

import uvicorn
from services.healthcheck import HealthChecker
from utils.middleware import GatewayMiddleware
from endpoints import api
from config import get_settings
from core import registry,balancer
setting = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    
    # 启动健康检查
    checker = HealthChecker(registry)
    asyncio.create_task(checker.start()) 
    yield
    

app = FastAPI(lifespan=lifespan)
app.include_router(api.router)
# 添加中间件（必须放在路由注册之后）
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