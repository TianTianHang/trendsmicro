from typing import Optional
from pydantic import BaseModel

class FitRequest(BaseModel):
    timespans: list[float]
    values: list[float]
class FitResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[dict] = None
    progress: Optional[float] = None