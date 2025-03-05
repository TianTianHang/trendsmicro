import socket
from fastapi import FastAPI
import asyncio
from services.rabbitmq import RabbitMQClient
from config import get_settings

from api.endpoints import user
from api.dependencies.database import engine, Base
from config import get_settings

from services.registry import ConsulRegistry, ServiceInstance

# 配置信息
settings = get_settings()
registry = ConsulRegistry(host=settings.consul_host, port=settings.consul_port)
hostname=socket.gethostname()
# 注册服务到Consul
instance = ServiceInstance(
        service_name="user_management",
        instance_id=f"user_management-{hostname}",
        host=socket.gethostbyname(hostname),
        port=settings.port,
    )


async def publish_public_key_periodically():
    while True:
        try:
            with open(settings.public_key_path, "r") as key_file:
                public_key = key_file.read()
            
            async with RabbitMQClient("public_key_queue") as client:
                await client.publish(public_key)
               
            
            # 每隔60秒发布一次
            await asyncio.sleep(60)
        except Exception as e:
            print(f"Error publishing public key: {e}")
            await asyncio.sleep(10)  # 出错后等待10秒重试
            
async def lifespan_handler(app: FastAPI):
    # 启动后台任务定期发布公钥
    asyncio.create_task(publish_public_key_periodically())
    
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
    uvicorn.run(app, host="0.0.0.0", port=settings.port)
