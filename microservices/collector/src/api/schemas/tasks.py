from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel

class HistoricalTaskRequest(BaseModel):
    job_type:str
    keywords: List[str]
    geo_code: str = ""
    start_date: date
    end_date: date
    interval: Optional[str] = None

class ScheduledTaskRequest(BaseModel):
    job_type:str
    keywords: List[str]
    geo_code: str = ""
    start_date: date
    duration: int
    interval: str = None

class HistoricalTaskResponse(BaseModel):
    id: int
    job_type: str
    keywords: List[str]
    status: str
    created_at: datetime

class ScheduledTaskResponse(BaseModel):
    id: int
    duration: int
    interval: str = None
    keywords: List[str]
    enabled: bool
