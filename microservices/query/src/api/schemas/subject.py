from datetime import datetime
from typing import List, Union
from pydantic import BaseModel



class RealtimeTask(BaseModel):
    type: str = "realtime"
    data_type: str
    keywords: List[str]
    geo_code: str
    start_date: datetime
    duration: int
    interval: str
   
# 定义历史数据查询任务模型
class HistoricalTask(BaseModel):
    type: str = "historical"
    data_type: str
    keywords: List[str]
    geo_code: str
    start_date: datetime
    end_date: datetime
    interval: str
   
class SubjectCreate(BaseModel):
    user_id: str
    parameters: List[Union[RealtimeTask,HistoricalTask]]
class SubjectResponse(BaseModel):
    subject_id: int



class SubjectDataResponse(BaseModel):
    subject_id: int
    timestamp: str
    data: dict
    