from typing import Dict, List
from models.service import ServiceInstance

class ServiceRegistry:
    def __init__(self):
        self.services: Dict[str, List[ServiceInstance]] = {}

    def register(self, instance: ServiceInstance):
        if instance.service_name not in self.services:
            self.services[instance.service_name] = []
        self.services[instance.service_name].append(instance)

    def deregister(self, service_name: str, instance_id: str):
        self.services[service_name] = [
            inst for inst in self.services.get(service_name, [])
            if inst.instance_id != instance_id
        ]

    def get_healthy_instances(self, service_name: str) -> List[ServiceInstance]:
        return [
            inst for inst in self.services.get(service_name, [])
            if inst.is_healthy
        ]