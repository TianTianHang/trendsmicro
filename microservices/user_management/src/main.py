import socket
from fastapi import FastAPI
from fastapi.logger import logger
from api.endpoints import user
import httpx
from api.dependencies.database import engine, Base
from config import get_settings
from tenacity import retry, stop_after_attempt

from api.models.permission import RoutePermission, ServicePermissionsResponse

# 配置信息
setting = get_settings()

# 服务注册信息
service_info = {
    "service_name": "user_management",
    "instance_id": f"user-{socket.gethostname()}",
    "host": "localhost",
    "port": setting.port,
    "health_check_url": f"http://localhost:{setting.port}/health"
}

# 路由权限信息
permissions = [
        RoutePermission(path="/register", required_permission=["public"]),
        RoutePermission(path="/token", required_permission=["public"]),  # 公开接口
        RoutePermission(path="/users/me", required_permission=["user","admin"]),
        RoutePermission(path="/users", required_permission=["admin"]),
        RoutePermission(path="/verify-token", required_permission=["public"]),
    ]


# -------------------- 服务注册逻辑 --------------------
@retry(stop=stop_after_attempt(3))
async def register_service():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{setting.api_gateway}/_internal/register",
                json=service_info,
                timeout=5
            )
            if response.status_code != 200:
                logger.warning("⚠️ 服务注册失败")
        except Exception as e:
            logger.error(f"🚨 无法连接网关: {str(e)}")

@retry(stop=stop_after_attempt(3))
async def deregister_service():
    async with httpx.AsyncClient() as client:
        try:         
            await client.delete(
                f"{setting.api_gateway}/_internal/deregister/user_management/user-{socket.gethostname()}"
            )
            logger.info("服务实例注销成功")
        except Exception as e:
            logger.error("注销失败")

async def lifespan_handler(app: FastAPI):
    try:
        await register_service()
    except Exception as e:
        logger.error(e)
    yield
    try:
        await deregister_service()
    except Exception as e:
        logger.error(e)

# -------------------- 应用初始化 --------------------
Base.metadata.create_all(bind=engine)
app = FastAPI(title="User Management API", lifespan=lifespan_handler)
app.include_router(user.router)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/permissions", response_model=ServicePermissionsResponse)
async def get_service_permissions():
    """
    返回当前服务的路由权限配置
    """
    # 返回服务权限配置
    return ServicePermissionsResponse(service_name=service_info["service_name"], permissions=permissions)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=setting.port)