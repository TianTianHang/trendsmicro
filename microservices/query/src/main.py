import socket
from fastapi import FastAPI, logger
import httpx
from tenacity import retry, stop_after_attempt
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config import get_settings
from api.dependencies.database import Base,engine
from api.endpoints import interest
from api.services.sync import SyncService

setting= get_settings()
service_info = {
        "service_name": "query",
        "instance_id": f"query-{socket.gethostname()}",
        "host": "localhost",
        "port": setting.port,
        "health_check_url": f"http://localhost:{setting.port}/health"
    }

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
    await register_service()
    yield
    await deregister_service()
   
            
Base.metadata.create_all(bind=engine)          
app = FastAPI(title="Query API",lifespan=lifespan_handler)

app.include_router(interest.router)



@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=setting.port)
