from fastapi import APIRouter, HTTPException
from models.service import ServiceInstance
from services.registry import ServiceRegistry

router = APIRouter(prefix="/_internal")
registry = ServiceRegistry()

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