import httpx
from fastapi import HTTPException
from api.config import get_settings

class CollectorGateway:
    def __init__(self):
        self.settings = get_settings()
        self.client = httpx.AsyncClient(base_url=self.settings.collector_url)

    async def get_region_interests(self) -> list[dict]:
        try:
            response = await self.client.get("/api/region-interests")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail="Failed to fetch region interests from collector"
            )

    async def get_time_interests(self) -> list[dict]:
        try:
            response = await self.client.get("/api/time-interests")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail="Failed to fetch time interests from collector"
            )

def get_gateway() -> CollectorGateway:
    return CollectorGateway()
