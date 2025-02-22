
from fastapi import APIRouter

from core import registry
router = APIRouter(prefix="/_internal")



@router.get("/services")
def list_services():
    return {
        "services": {
            name: [inst.model_dump() for inst in instances]
            for name, instances in registry.services.items()
        }
    }
    
