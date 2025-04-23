import asyncio
import socket
import aio_pika
from fastapi import Body, Depends, FastAPI, HTTPException, Header, Path, Query
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from jose import JWTError, jwt
from pydantic import BaseModel
from config import get_settings
from services.rabbitmq import RabbitMQClient
from services.jwt_validator import JWTValidator
from services.registry import ServiceInstance,ConsulRegistry
from dependencies.database import engine, Base,get_db
from sqlalchemy.orm import Session
from models.permission import Permission

setting = get_settings()
registry = ConsulRegistry(host=setting.consul_host, port=setting.consul_port)
jwt_validatort = JWTValidator()

hostname=socket.gethostname()
# 注册服务到Consul
instance = ServiceInstance(
        service_name="permission",
        instance_id=f"permission-{hostname}",
        host=socket.gethostbyname(hostname),
        port=setting.port,
       
    )
@RabbitMQClient.consumer(queue="public_key_queue")
async def on_message(message: aio_pika.IncomingMessage):
    async with message.process():
        aio_pika.logger.info("已收到公钥")
        public_key = message.body.decode()
        jwt_validatort.public_key=public_key
        
@asynccontextmanager
async def lifespan(app: FastAPI):
   
    await RabbitMQClient.start_consumers(app)
    registry.register(instance)
    yield
    # 注销服务
    registry.deregister(instance.service_name, instance.instance_id)
    await RabbitMQClient.close_consumers(app)
    
Base.metadata.create_all(bind=engine)    
app = FastAPI(lifespan=lifespan)



@app.get("/health")
async def health_check():
    return {"status": "healthy"}

class PermissionCreate(BaseModel):
    service_name: str
    path: str
    required_permission: str

class PermissionUpdate(BaseModel):
    path:str
    required_permission: str

class VerifyPermission(BaseModel):
    service_name:str
    path:str
    
@app.get("/permissions/list")
async def list_permissions(db: Session = Depends(get_db)):
    permissions = db.query(Permission).order_by(Permission.service_name).all()
    return [{
        "service_name": p.service_name,
        "path": p.path,
        "required_permission": p.required_permission.split(',')
    } for p in permissions]

@app.post("/permissions/create")
async def create_permission(
    permission: PermissionCreate,
    db: Session = Depends(get_db)
):
    # 检查权限是否已存在
    existing = db.query(Permission).filter(
        Permission.service_name == permission.service_name,
        Permission.path == permission.path
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Permission already exists")

    new_permission = Permission(
        service_name=permission.service_name,
        path=permission.path,
        required_permission=permission.required_permission
    )
    db.add(new_permission)
    db.commit()
    return {"message": "Permission created successfully"}

@app.delete("/permissions/{service_name}/delete")
async def delete_permission(
    path: str = Query(..., description="路径"),
    service_name: str = Path(..., description="服务名称"),
    db: Session = Depends(get_db)
):
    db_permission = db.query(Permission).filter(
        Permission.service_name == service_name,
        Permission.path == path
    ).first()
    if not db_permission:
        raise HTTPException(status_code=404, detail="Permission not found")

    db.delete(db_permission)
    db.commit()
    return {"message": "Permission deleted successfully"}

@app.put("/permissions/{service_name}/update")
async def update_permission(
    permission: PermissionUpdate,
    service_name: str = Path(..., description="服务名称"),
    db: Session = Depends(get_db)
):
    db_permission = db.query(Permission).filter(
        Permission.service_name == service_name,
        Permission.path == permission.path
    ).first()
    if not db_permission:
        raise HTTPException(status_code=404, detail="Permission not found")

    db_permission.required_permission = permission.required_permission
    db.commit()
    return {"message": "Permission updated successfully"}


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
            token_roles:list[str] = payload.get("roles")
            # print(token_roles)
        elif payload is False:
            raise HTTPException(status_code=401, detail="No public key")
        else:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token validation failed")
    if permission:
        required_permission = permission.required_permission.split(',')
        if set(token_roles) & set(required_permission):
            return {"message": "Permission granted"}
        else:
            raise HTTPException(status_code=403, detail="Permission denied")
    else:
        raise HTTPException(status_code=404, detail="Path not found")
    
    
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=setting.port)

