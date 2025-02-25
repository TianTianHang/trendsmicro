from datetime import datetime
from typing import List, Optional, Union
import httpx
from pydantic import BaseModel
from services.registry import ConsulRegistry, ServiceInstance
import json
# 请求模型
class HistoricalTaskRequest(BaseModel):
    job_type:str
    keywords: List[str]
    geo_code: str = ""
    start_date: str
    end_date: str
    interval: Optional[str] = None

class ScheduledTaskRequest(BaseModel):
    job_type:str
    keywords: List[str]
    geo_code: str = ""
    start_date: str
    duration: int
    interval: str = None
    
class CollectorService:
    def __init__(self, registry: ConsulRegistry):
        self.registry = registry

    def get_collector_instance(self) -> Optional[ServiceInstance]:
        instances = self.registry.get_healthy_instances("trends_collector")
        if instances:
            return instances[0]
        return None

    async def add_task(self, req: Union[HistoricalTaskRequest,ScheduledTaskRequest]) -> Optional[dict]:
        instance = self.get_collector_instance()
        if not instance:
            return None
        if isinstance(req, HistoricalTaskRequest):
            endpoint = "tasks/historical"
        elif isinstance(req, ScheduledTaskRequest):
            endpoint = "tasks/scheduled" 
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
    