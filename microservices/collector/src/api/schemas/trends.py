from datetime import datetime, date
from typing import List, Dict, Any
from pydantic import BaseModel

class TrendsByRegionRequest(BaseModel):
    keywords: List[str]
    geo_code: str = "world"
    start_date: date
    end_date: date
    interval: str = "month"

class TrendsOverTimeRequest(BaseModel):
    keywords: List[str]
    geo_code: str = "world"
    start_date: date
    end_date: date
    interval: str = "month"

class RegionTrendsData(BaseModel):
    geo_code: str
    timeframe_start: date
    timeframe_end: date
    data: List[Dict[str, Any]]

class TimeTrendsData(BaseModel):
    geo_code: str
    timeframe_start: date
    timeframe_end: date
    data: List[Dict[str, Any]]

class RegionTrendsResponse(BaseModel):
    task_id: int
    interest_ids: List[int]
    data: List[RegionTrendsData]
    status: str = "success"

class TimeTrendsResponse(BaseModel):
    task_id: int
    interest_ids: List[int]
    data: List[TimeTrendsData]
    status: str = "success"