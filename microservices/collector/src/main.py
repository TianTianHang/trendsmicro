#src/api/main.py
import logging
import socket
from fastapi import FastAPI
from services.rabbitmq import RabbitMQClient
from services import registry
from api.dependencies.database import engine,Base
from core import aio_scheduler
from fastapi_events.middleware import EventHandlerASGIMiddleware
from fastapi_events.handlers.local import local_handler
from api.endpoints import tasks
from config import get_settings
import handlers
from services.registry import ServiceInstance
# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(),  # 输出到控制台
        logging.FileHandler("collector.log"),  # 输出到文件
    ]
)

setting= get_settings()

hostname=socket.gethostname()
# 注册服务到Consul
instance = ServiceInstance(
        service_name="trends_collector",
        instance_id=f"trends_collector-{hostname}",
        host=socket.gethostbyname(hostname),
        port=setting.port,
       
    )


            
          
async def lifespan_handler(app: FastAPI):
    await RabbitMQClient.start_consumers(app)
    aio_scheduler.start()
    registry.register(instance)
    yield
    # 注销服务
    registry.deregister(instance.service_name, instance.instance_id)
    aio_scheduler.scheduler.shutdown()
    await RabbitMQClient.close_consumers(app)

    
    
    
Base.metadata.create_all(bind=engine)
# 新增状态同步
# scheduler_manager.sync_job_status()
app = FastAPI(title="Trends Collector API",lifespan=lifespan_handler)
app.add_middleware(EventHandlerASGIMiddleware, 
                   handlers=[local_handler],middleware_id=8888)
app.include_router(tasks.router)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=setting.port)
