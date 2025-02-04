from datetime import date, datetime
from typing import List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from api.models.interest import RegionInterest
from api.dependencies.database import get_db
from api.models.interest import TimeInterest
router = APIRouter(prefix="/interest")

class RegionInterestResponse(BaseModel):
    id: int
    keyword: str
    geo_code: str
    timeframe_start: Optional[date]
    timeframe_end: Optional[date]
    value: int

    class Config:
        from_attributes = True

class TimeInterestResponse(BaseModel):
    id: int
    keyword: str
    geo_code: Optional[str]
    time: date
    value: int
    is_partial: Optional[bool]

    class Config:
        from_attributes = True

@router.get("/region-interests/", response_model=List[RegionInterestResponse])
def get_region_interests(
    keyword: Optional[str] = None,
    geo_code: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(RegionInterest)
    if keyword:
        query = query.filter(RegionInterest.keyword == keyword)
    if geo_code:
        query = query.filter(RegionInterest.geo_code == geo_code)
    return query.all()

@router.get("/time-interests/", response_model=List[TimeInterestResponse])
def get_time_interests(
    keyword: Optional[str] = None,
    geo_code: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(TimeInterest)
    if keyword:
        query = query.filter(TimeInterest.keyword == keyword)
    if geo_code:
        query = query.filter(TimeInterest.geo_code == geo_code)
    return query.all()