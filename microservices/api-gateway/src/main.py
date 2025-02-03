# app/main.py
from fastapi import FastAPI
from contextlib import asynccontextmanager
import asyncio

import uvicorn
from services.registry import ServiceRegistry
from services.healthcheck import HealthChecker
from utils.load_balancer import RoundRobinBalancer
from utils.middleware import GatewayMiddleware
from endpoints import api
from config import get_settings
setting = get_settings()
# 初始化核心组件
registry = ServiceRegistry()
balancer = RoundRobinBalancer()

@asynccontextmanager
async def lifespan(app: FastAPI):
    
    # 启动健康检查
    checker = HealthChecker(registry)
    asyncio.create_task(checker.start())   
    yield
    

app = FastAPI(lifespan=lifespan)
app.include_router(api.router, prefix="/_internal")
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