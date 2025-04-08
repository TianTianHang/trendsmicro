import socket
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from config import get_settings
from api.dependencies.database import Base,engine

from fastapi_events.middleware import EventHandlerASGIMiddleware
from fastapi_events.handlers.local import local_handler
from services.rabbitmq import RabbitMQClient
from services import registry
from services.registry import ServiceInstance
from api.endpoints import subject
from api.endpoints import subjectData
from api.endpoints import keywords
from api.endpoints import cfc
from api.endpoints import moran
from api.endpoints import interests
from api.endpoints import layouts
from api.endpoints import datasource
import handlers


settings= get_settings()

hostname=socket.gethostname()
# 注册服务到Consul
instance = ServiceInstance(
        service_name="query",
        instance_id=f"query-{hostname}",
        host=socket.gethostbyname(hostname),
        port=settings.port
    )        
            
async def lifespan_handler(app: FastAPI):
    await RabbitMQClient.start_consumers(app)
    registry.register(instance)
    yield
    # 注销服务
    registry.deregister(instance.service_name, instance.instance_id)
    await RabbitMQClient.close_consumers(app)
            
Base.metadata.create_all(bind=engine)          
app = FastAPI(title="Query API",lifespan=lifespan_handler)

app.add_middleware(EventHandlerASGIMiddleware, 
                   handlers=[local_handler])

app.include_router(cfc.router)
app.include_router(moran.router)
app.include_router(subject.router)
app.include_router(keywords.router)
app.include_router(subjectData.router)
app.include_router(interests.router)
app.include_router(layouts.router)
app.include_router(datasource.router)

@app.get("/health")
async def health_check():
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
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.port)
