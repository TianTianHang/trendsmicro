from datetime import datetime
from fastapi import APIRouter, HTTPException
from models.service import ServiceInstance
from core import registry
router = APIRouter(prefix="/_internal")


@router.post("/register")
async def register_service(instance: ServiceInstance):
    existing = [i for i in registry.services.get(instance.service_name, [])
                if i.instance_id == instance.instance_id]
    
    if existing:
        raise HTTPException(status_code=400, detail="Instance already registered")
    
    registry.register(instance)
    return {"status": "registered"}

@router.delete("/deregister/{service_name}/{instance_id}")
async def deregister_service(service_name: str, instance_id: str):
    registry.deregister(service_name, instance_id)
    return {"status": "removed"}

@router.get("/services")
def list_services():
    return {
        "services": {
            name: [inst.model_dump() for inst in instances]
            for name, instances in registry.services.items()
        }
    }
    
    # 添加心跳接口
@router.post("/heartbeat/{instance_id}")
async def send_heartbeat(instance_id: str):
    for service in registry.services.values():
        for inst in service:
            if inst.instance_id == instance_id:
                inst.last_health_check = datetime.now()
                return {"status": "updated"}
    return {"status": "not_found"}