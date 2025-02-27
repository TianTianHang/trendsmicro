import asyncio
import socket
from fastapi import Depends, FastAPI, HTTPException, Header
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from jose import JWTError, jwt
from pydantic import BaseModel
from config import get_settings
from services.jwt_validator import JWTValidator
from services.registry import ServiceInstance,ConsulRegistry
from dependencies.database import engine, Base,get_db
from sqlalchemy.orm import Session
from models.permission import Permission

setting = get_settings()
registry = ConsulRegistry(host=setting.consul_host, port=setting.consul_port)
jwt_validatort = JWTValidator(registry)

hostname=socket.gethostname()
# 注册服务到Consul
instance = ServiceInstance(
        service_name="permission",
        instance_id=f"permission-{hostname}",
        host=socket.gethostbyname(hostname),
        port=setting.port,
       
    )

@asynccontextmanager
async def lifespan(app: FastAPI):
   
    asyncio.create_task(jwt_validatort.periodic_refresh())
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
    permissions = db.query(Permission).filter(
        Permission.service_name == req.service_name
    ).all()

    permission = None
   
    for perm in permissions:
        perm_path_parts = perm.path.split('/')
        req_path_parts = req.path.split('/')
        if len(perm_path_parts) == len(req_path_parts):
            match = True
            for perm_part, req_part in zip(perm_path_parts, req_path_parts):
                if perm_part.startswith('{') and perm_part.endswith('}'):
                    continue
                if perm_part != req_part:
                    match = False
                    break
            if match:
                permission = perm
                break
   
    if permission and "public" in permission.required_permission.split(','):
        return {"message": "Permission granted"}
   
    if not authorization or "Bearer " not in authorization:
            return JSONResponse(
            status_code=401,
            content={"message": "Missing or invalid Authorization head·er"}
            )
    token = authorization.split("Bearer ")[-1]
    
    try:
        # 验证JWT令牌
        payload =await jwt_validatort.verify_token(token)
        if payload:
            username: str = payload.get("sub")
            if not username:
                raise HTTPException(status_code=401, detail="Invalid token")
            token_role = payload.get("role")
        elif payload is False:
            raise HTTPException(status_code=401, detail="No public key")
        else:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token validation failed")
    if permission:
        required_permission = permission.required_permission.split(',')
        if token_role in required_permission:
            return {"message": "Permission granted"}
        else:
            raise HTTPException(status_code=403, detail="Permission denied")
    else:
        raise HTTPException(status_code=404, detail="Path not found")
    
    
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=setting.port)
