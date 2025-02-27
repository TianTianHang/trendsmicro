import socket
from fastapi import FastAPI
from api.endpoints import user
from api.dependencies.database import engine, Base
from config import get_settings

from services.registry import ConsulRegistry, ServiceInstance

# 配置信息
setting = get_settings()
registry = ConsulRegistry(host=setting.consul_host, port=setting.consul_port)
hostname=socket.gethostname()
# 注册服务到Consul
instance = ServiceInstance(
        service_name="user_management",
        instance_id=f"user_management-{hostname}",
        host=socket.gethostbyname(hostname),
        port=setting.port,
    )



async def lifespan_handler(app: FastAPI):
    
    registry.register(instance)
    yield
    registry.deregister(instance.service_name, instance.instance_id)

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