
import json
from typing import Optional

import httpx
from services.registry import ConsulRegistry, ServiceInstance


class QueryService:
    def __init__(self, registry: ConsulRegistry):
        self.registry = registry

    def get_instance(self) -> Optional[ServiceInstance]:
        instances = self.registry.get_healthy_instances("query")
        if instances:
            return instances[0]
        return None

    async def task_finish(self, req) -> Optional[dict]:
        instance = self.get_collector_instance()
        if not instance:
            return None
        endpoint="subject/finish"
        url = f"http://{instance.host}:{instance.port}/{endpoint}"
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=json.loads(req.model_dump_json()),
                headers={"Content-Type": "application/json"}
            )
            if response.status_code == 200:
                return response.json()
            return None
    