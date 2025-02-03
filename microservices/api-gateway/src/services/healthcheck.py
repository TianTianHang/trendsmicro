import httpx
import asyncio
from datetime import datetime
from config import get_settings
from services.registry import ServiceRegistry
setting = get_settings()
class HealthChecker:
    def __init__(self, registry: ServiceRegistry):
        self.registry = registry
        self.check_interval = setting.health_check_interval  # 检查间隔秒数

    async def start(self):
        while True:
            await self.check_all_services()
            await asyncio.sleep(self.check_interval)

    async def check_all_services(self):
        async with httpx.AsyncClient() as client:
            for service_name, instances in self.registry.services.items():
                for instance in instances:
                    try:
                        response = await client.get(
                            instance.health_check_url,
                            timeout=3
                        )
                        instance.is_healthy = response.status_code == 200
                    except Exception:
                        instance.is_healthy = False
                    finally:
                        instance.last_health_check = datetime.now()