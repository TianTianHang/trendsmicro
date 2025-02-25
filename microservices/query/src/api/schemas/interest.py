from pydantic import BaseModel
from datetime import date
from typing import Optional

class RegionInterestBase(BaseModel):
    keyword: str
    geo_code: str
    timeframe_start: Optional[date] = None
    timeframe_end: Optional[date] = None
    value: Optional[int] = None

class RegionInterestCreate(RegionInterestBase):
    pass

class RegionInterestRespone(RegionInterestBase):
    id: int
    class Config:
        from_attribute = True
    
    
    
class TimeInterestResponseBase(BaseModel):
    keyword: str
    geo_code: Optional[str] = None
    time: date
    value: int
    is_partial: Optional[bool] = None

class TimeInterestResponseCreate(TimeInterestResponseBase):
    pass

class TimeInterestResponse(TimeInterestResponseBase):
    id: int
    
    class Config:
        from_attribute = True
class InterestMetaData(BaseModel):
    keywords: list[str]
    geo_code: str
    timeframe_start: date
    timeframe_end: date
