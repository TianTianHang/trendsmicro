
from fastapi import APIRouter

from core import registry
router = APIRouter(prefix="/_internal")



@router.get("/services")
def list_services(service_name: str):
    return {
        "services": registry.get_healthy_instances(service_name)
    }
