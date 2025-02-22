import socket
from fastapi import FastAPI
from api.endpoints import user
from api.dependencies.database import engine, Base
from config import get_settings

from api.models.permission import RoutePermission, ServicePermissionsResponse
from services.registry import ConsulRegistry, ServiceInstance

# 配置信息
setting = get_settings()
registry = ConsulRegistry(host=setting.consul_host, port=setting.consul_port)
hostname=socket.gethostname()
# 注册服务到Consul
instance = ServiceInstance(
        service_name="user_management",
        instance_id=f"user_management-{hostname}",
        host=hostname,
        port=setting.port,
    )

# 路由权限信息
permissions = [
        RoutePermission(path="/register", required_permission=["public"]),
        RoutePermission(path="/token", required_permission=["public"]),  # 公开接口
        RoutePermission(path="/users/me", required_permission=["user","admin"]),
        RoutePermission(path="/users", required_permission=["admin"]),
        RoutePermission(path="/verify-token", required_permission=["public"]),
    ]


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

@app.get("/permissions", response_model=ServicePermissionsResponse)
async def get_service_permissions():
    """
    返回当前服务的路由权限配置
    """
    # 返回服务权限配置
    return ServicePermissionsResponse(service_name=instance.service_name, permissions=permissions)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=setting.port)