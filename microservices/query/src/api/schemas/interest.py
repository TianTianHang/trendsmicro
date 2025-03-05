from pydantic import BaseModel, Field
from datetime import date
from typing import Optional


class TimeInterest(BaseModel):
    time_utc: str 
    is_partial: Optional[bool] = False
    
    # 多出来的键是关键字，可能有多个
    class Config:
        extra = "allow"
        
    def convert(self,collect_id:int):
        from api.models.interest import TimeInterest as TimeModel
        return TimeModel(time_utc=self.time_utc,is_partial=self.is_partial,collect_id=collect_id,
                         values=self.model_dump(exclude={'time_utc','is_partial'}))
        
class RegionInterest(BaseModel):
    geo_name: str
    geo_code: str
    def convert(self,collect_id:int):
        from api.models.interest import RegionInterest as RegionModel
        return RegionModel(geo_name=self.geo_name,geo_code=self.geo_code,collect_id=collect_id,
                           values=self.model_dump(exclude={'geo_name','geo_code'}))

    class Config:
        extra = "allow"
       
        
class InterestMetaData(BaseModel):
    keywords: list[str]
    geo_code: str
    timeframe_start: date
    timeframe_end: date
   
    def convert(self,subject_data_id:int):
        from api.models.interest import InterestMetaData as MetaModel
        return MetaModel(
             keywords = self.keywords,
            geo_code = self.geo_code,
            timeframe_start = self.timeframe_start,
            timeframe_end = self.timeframe_end,
            subject_data_id = subject_data_id)
