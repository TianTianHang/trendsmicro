import consul
from typing import Dict, List, Optional
from pydantic import BaseModel
from datetime import datetime

class ServiceInstance(BaseModel):
    service_name: str
    instance_id: str
    host: str
    port: int
    health_check_url: str= None
    last_health_check: datetime = None
    is_healthy: bool = False
    heartbeat_interval: int = 30  # 服务主动上报间隔
    
class ConsulRegistry:
    def __init__(self, host: str = 'consul', port: int = 8500):
        self.client = consul.Consul(host=host, port=port)

    def register(self, instance: ServiceInstance):
        service_id = f"{instance.service_name}-{instance.instance_id}"
        self.client.agent.service.register(
            name=instance.service_name,
            service_id=service_id,
            address=instance.host,
            port=instance.port,
            check=consul.Check.http(
                instance.health_check_url if instance.health_check_url else f"http://{instance.host}:{instance.port}/health",
                interval="10s"
            )
        )

    def deregister(self, service_name: str, instance_id: str):
        service_id = f"{service_name}-{instance_id}"
        self.client.agent.service.deregister(service_id)

    def get_healthy_instances(self, service_name: str) -> List[ServiceInstance]:
        _, services = self.client.health.service(service_name)
        return [
            ServiceInstance(
                service_name=service['Service']['Service'],
                instance_id=service['Service']['ID'],
                host=service['Service']['Address'],
                port=service['Service']['Port'],
                is_healthy=all(check['Status'] == 'passing' for check in service['Checks'])
            )
            for service in services
        ]
