import socket
from fastapi import FastAPI
from fastapi.logger import logger
import httpx
from tenacity import retry, stop_after_attempt
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config import get_settings
from api.dependencies.database import Base,engine
from api.endpoints import interest
from services.sync import SyncService
from services.registry import ConsulRegistry
from api.models.permission import RoutePermission, ServicePermissionsResponse
from api.endpoints import cfc
from api.endpoints import moran

setting= get_settings()
service_info = {
        "service_name": "query",
        "instance_id": f"query-{socket.gethostname()}",
        "host": "localhost",
        "port": setting.port,
        "health_check_url": f"http://localhost:{setting.port}/health"
    }
ConsulRegistry=ConsulRegistry()
service_permissions = ServicePermissionsResponse(
    service_name="query",
    permissions=[
        # Interest endpoints
        RoutePermission(
            path="/interest/region-interests/timeframes",
            required_permission=["user","admin"],
        ),
        RoutePermission(
            path="/interest/region-interests/geo-time-slices",
            required_permission=["user","admin"],
        ),
        RoutePermission(
            path="/interest/time-interests/",
            required_permission=["user","admin"],
        ),
        # CFC endpoints
        RoutePermission(
            path="/cfc/train",
            required_permission=["user","admin"],
        ),
        RoutePermission(
            path="/cfc/predict",
            required_permission=["user","admin"],
        ),
        RoutePermission(
            path="/cfc/fit",
            required_permission=["user","admin"],
        ),
        RoutePermission(
            path="/cfc/fit/{task_id}",
            required_permission=["user","admin"],
        ),
        # Moran's I endpoints
        RoutePermission(
            path="/moran/global",
            required_permission=["user","admin"],
        ),
        RoutePermission(
            path="/moran/local",
            required_permission=["user","admin"],
        )
    ]
)

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
            f"{setting.api_gateway}/_internal/deregister/query/query-{socket.gethostname()}"
        )
            logger.info("服务实例注销成功")
        except Exception as e:
            logger.error("注销失败")
            
            
async def lifespan_handler(app: FastAPI):
    sync_service = SyncService()
    scheduler = AsyncIOScheduler()
    # 每10分钟同步一次
    scheduler.add_job(sync_service.sync_all_data, 'interval', minutes=10)
    scheduler.start()
    try:
        await register_service()
    except Exception as e:
        logger.error(e)
    yield
    try:
        await deregister_service()
    except Exception as e:
        logger.error(e)
            
Base.metadata.create_all(bind=engine)          
app = FastAPI(title="Query API",lifespan=lifespan_handler)

app.include_router(interest.router)
app.include_router(cfc.router)
app.include_router(moran.router)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
@app.get("/permissions", response_model=ServicePermissionsResponse)
async def get_task_permissions():
    """返回任务服务的权限配置"""    
    return service_permissions
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=setting.port)
