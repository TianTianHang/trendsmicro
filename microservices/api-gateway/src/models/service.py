from pydantic import BaseModel
from datetime import datetime

class ServiceInstance(BaseModel):
    service_name: str
    instance_id: str
    host: str
    port: int
    health_check_url: str
    last_health_check: datetime = None
    is_healthy: bool = False