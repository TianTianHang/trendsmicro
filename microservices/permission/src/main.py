import socket
from fastapi import Depends, FastAPI, HTTPException, Header, Request
from fastapi.responses import JSONResponse
import httpx
from contextlib import asynccontextmanager

from pydantic import BaseModel
from config import get_settings
from services.registry import ServiceInstance,ConsulRegistry
from dependencies.database import engine, Base,get_db
from sqlalchemy.orm import Session
from models.permission import Permission

setting = get_settings()
registry = ConsulRegistry(host=setting.consul_host, port=setting.consul_port)
hostname=socket.gethostname()
# 注册服务到Consul
instance = ServiceInstance(
        service_name="permission",
        instance_id=f"permission-{hostname}",
        host=hostname,
        port=setting.port,
       
    )

@asynccontextmanager
async def lifespan(app: FastAPI):
   
    
    registry.register(instance)
    yield
    # 注销服务
    registry.deregister(instance.service_name, instance.instance_id)
Base.metadata.create_all(bind=engine)    
app = FastAPI(lifespan=lifespan)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}

class VerifyPermission(BaseModel):
    service_name:str
    path:str
    
@app.post("/verify-permission")
async def verify_permission(req: VerifyPermission, authorization: str = Header(None), db: Session = Depends(get_db)):
    # Check if the path is public
    permission = db.query(Permission).filter(Permission.path == req.path, Permission.service_name == req.service_name).first()
    if permission and "public" in permission.required_permission.split(','):
        return {"message": "Permission granted"}
   
    if not authorization or "Bearer " not in authorization:
            return JSONResponse(
            status_code=401,
            content={"message": "Missing or invalid Authorization head·er"}
            )
    token = authorization.split("Bearer ")[-1]
    
    instances = registry.get_healthy_instances("user_management")
    if not instances:
        raise HTTPException(status_code=401, detail="User management service unavailable") # 返回 None 表示没有可用实例

    # 获取第一个健康实例的 URL
    target = instances[0]
    verify_token_url=f"http://{target.host}:{target.port}/verify-token"
    try:
        async with httpx.AsyncClient() as client:
                response = await client.post(
                    verify_token_url,
                    json={"token": token},
                    headers={"Content-Type": "application/json"}
                )
                user_info = response.json()
                token_role =user_info.get("role")
                if response.status_code != 200:
                    return JSONResponse(
                        status_code=response.status_code,
                        content={"message": response.json().get("detail", "Token validation failed")}
                    )
    except httpx.RequestError:
            return JSONResponse(
                status_code=503,
                content={"message": "User management service unavailable"}
            )
        
    if permission:
        required_permission = permission.required_permission.split(',')
        if token_role in required_permission:
            return {"message": "Permission granted", "user_info": user_info}
        else:
            raise HTTPException(status_code=403, detail="Permission denied")
    else:
        raise HTTPException(status_code=404, detail="Path not found")
    
    
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=setting.port)
