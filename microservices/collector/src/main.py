#src/api/main.py
from datetime import datetime
from json import JSONEncoder
import socket
from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from fastapi.logger import logger
import httpx
from api.dependencies.database import engine,Base
from api.dependencies.scheduler import scheduler_manager
from api.endpoints import tasks,interests
from config import get_settings
from tenacity import retry, stop_after_attempt

from api.models.permission import RoutePermission, ServicePermissionsResponse


setting= get_settings()

service_info = {
        "service_name": "trends_collector",
        "instance_id": f"trends-{socket.gethostname()}",
        "host": "localhost",
        "port": setting.port,
        "health_check_url": f"http://localhost:{setting.port}/health"
    }
service_permissions = ServicePermissionsResponse(
        service_name="trends_collector",
        permissions=[
            RoutePermission(
                path="/tasks/historical",
                required_permission=["admin"]
            ),
            RoutePermission(
                path="/tasks/scheduled",
                required_permission=["admin"]
            ),
           RoutePermission(
                path="/tasks/historical/{task_id}/terminate",
                required_permission=["admin"]
            ),
           RoutePermission(
                path="/tasks/scheduled/{task_id}/toggle",
                required_permission=["admin"]
            ),
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
            f"{setting.api_gateway}/_internal/deregister/trends_collector/trends-{socket.gethostname()}"
        )
            logger.info("服务实例注销成功")
        except Exception as e:
            logger.error("注销失败")
            
          
async def lifespan_handler(app: FastAPI):
    scheduler_manager.scheduler.start()
    # 新增状态同步
    scheduler_manager.sync_job_status()
    try:
        await register_service()
    except Exception as e:
        logger.error(e)
    yield
    try:
        await deregister_service()
    except Exception as e:
        logger.error(e)
    scheduler_manager.scheduler.shutdown()

    
    
    
Base.metadata.create_all(bind=engine)
app = FastAPI(title="Trends Collector API",lifespan=lifespan_handler)
app.include_router(tasks.router)
app.include_router(interests.router)

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