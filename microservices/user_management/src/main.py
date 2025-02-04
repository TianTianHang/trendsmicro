import socket
from fastapi import FastAPI
from fastapi.logger import logger
from api.endpoints import user
import httpx
from api.dependencies.database import engine, Base
from config import get_settings
from tenacity import retry, stop_after_attempt

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

# -------------------- 认证配置 --------------------

SECRET_KEY = setting.secret_key
ALGORITHM = setting.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = setting.access_token_expire_minutes


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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=setting.port)