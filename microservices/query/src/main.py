import socket
from fastapi import FastAPI
from config import get_settings
from api.dependencies.database import Base,engine

from fastapi_events.middleware import EventHandlerASGIMiddleware
from fastapi_events.handlers.local import local_handler
from services import registry
from services.registry import ServiceInstance
from api.endpoints import subject
from services import collector
from api.endpoints import cfc
from api.endpoints import moran
import handlers

setting= get_settings()

hostname=socket.gethostname()
# 注册服务到Consul
instance = ServiceInstance(
        service_name="query",
        instance_id=f"query-{hostname}",
        host=socket.gethostbyname(hostname),
        port=setting.port
    )        
            
async def lifespan_handler(app: FastAPI):
   
    registry.register(instance)
    yield
    # 注销服务
    registry.deregister(instance.service_name, instance.instance_id)
   
            
Base.metadata.create_all(bind=engine)          
app = FastAPI(title="Query API",lifespan=lifespan_handler)

app.add_middleware(EventHandlerASGIMiddleware, 
                   handlers=[local_handler])

app.include_router(cfc.router)
app.include_router(moran.router)
app.include_router(subject.router)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=setting.port)
