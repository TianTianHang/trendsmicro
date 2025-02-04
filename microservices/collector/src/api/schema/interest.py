from pydantic import BaseModel
from datetime import date
from typing import Optional

class RegionInterestSchema(BaseModel):
    id: Optional[int]
    keyword: str
    geo_code: str
    timeframe_start: Optional[date]
    timeframe_end: Optional[date]
    value: Optional[int]

   
        
class TimeInterestSchema(BaseModel):
    """时间兴趣数据的 Pydantic 模型"""
    id: Optional[int] = None
    keyword: str
    geo_code: Optional[str] = None
    time: date
    value: Optional[int] = None
    is_partial: Optional[bool] = None