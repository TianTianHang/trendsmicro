import httpx
import asyncio
from jose import JWTError, jwt

class JWTValidator:
    def __init__(self, registry, refresh_interval=3600):
        self.public_key = None
        self.registry = registry
        self.refresh_interval = refresh_interval
        

    async def periodic_refresh(self):
        while True:
            await self.fetch_public_keys()
            await asyncio.sleep(self.refresh_interval)

    async def fetch_public_keys(self):
        instances = self.registry.get_healthy_instances("user_management")
        if not instances:
            return None  # 返回 None 表示没有可用实例

        # 获取第一个健康实例的 URL
        target = instances[0]
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://{target.host}:{target.port}/public-key")
            self.public_key = response.json().get("public_key")

    async def verify_token(self, token: str):
        public_key = self.public_key
        if not public_key:
            return False
        try:
            payload = jwt.decode(token, public_key, algorithms=["RS256"])
            return payload
        except JWTError:
            return False