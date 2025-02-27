from datetime import date, datetime
from typing import List, Optional, Union
from pydantic import BaseModel, field_validator

from api.schemas.interest import InterestMetaData, RegionInterest, TimeInterest



class RealtimeTask(BaseModel):
    type: str = "realtime"
    data_type: str
    keywords: List[str]
    geo_code: str
    start_date: date
    duration: int
    interval: str
   
# 定义历史数据查询任务模型
class HistoricalTask(BaseModel):
    type: str = "historical"
    data_type: str
    keywords: List[str]
    geo_code: str
    start_date: date
    end_date: date
    interval: str =None
   
class SubjectCreate(BaseModel):
    user_id: int
    name: str
    description:str
    parameters: List[Union[RealtimeTask,HistoricalTask]]
class SubjectResponse(BaseModel):
    subject_id: int
    name: str
    description:Optional[str]
class SubjectListResponse(BaseModel):
    subject_id: int
    name: str
    description:Optional[str]
    status: str
    data_num: int

class SubjectDataResponse(BaseModel):
    subject_id: int
    timestamp: str
    meta: List[InterestMetaData]

class SubjectDataTimeResponse(SubjectDataResponse):
    data: List[List[TimeInterest]]

class SubjectDataRegionResponse(SubjectDataResponse):
    data: List[List[RegionInterest]]
    
class NotifyRequest(BaseModel):
    task_id: int
    type: str
    interest_type: str
    interests: list[str]
    meta: list[InterestMetaData]