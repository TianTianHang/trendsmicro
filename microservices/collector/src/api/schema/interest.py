from pydantic import BaseModel
from datetime import date
from typing import Optional
class InterestMetaData(BaseModel):
    keywords: list[str]
    geo_code: str
    timeframe_start: date
    timeframe_end: date
