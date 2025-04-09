from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from api.dependencies.database import get_db
from core.trends import get_interest_by_region, get_interest_over_time
from api.models.interest import RegionInterest, TimeInterest
from api.schemas.trends import (
    TrendsByRegionRequest,
    TrendsOverTimeRequest,
    RegionTrendsResponse,
    TimeTrendsResponse
)

router = APIRouter(prefix="/trends")

@router.post("/by-region", response_model=RegionTrendsResponse)
async def get_trends_by_region(
    request: TrendsByRegionRequest,
    db: Session = Depends(get_db)
):
    """获取按地区划分的Google Trends数据"""
    try:
        interest_ids = get_interest_by_region(
            keywords=request.keywords,
            geo_code=request.geo_code,
            interval=request.interval,
            start_date=request.start_date.strftime("%Y-%m-%d"),
            end_date=request.end_date.strftime("%Y-%m-%d"),
            task_id=None
        )
        
        # 查询数据库获取实际数据
        records = db.query(RegionInterest).filter(
            RegionInterest.id.in_(interest_ids)
        ).all()
        
        data = [
            {
                "geo_code": record.geo_code,
                "timeframe_start": record.timeframe_start,
                "timeframe_end": record.timeframe_end,
                "data": record.data
            }
            for record in records
        ]
        
        return RegionTrendsResponse(
            task_id=None,
            interest_ids=interest_ids,
            data=data
        )
    except Exception as e:
        raise HTTPException(500, str(e))

@router.post("/over-time", response_model=TimeTrendsResponse)
async def get_trends_over_time(
    request: TrendsOverTimeRequest,
    db: Session = Depends(get_db)
):
    """获取随时间变化的Google Trends数据"""
    try:
        interest_ids = get_interest_over_time(
            keywords=request.keywords,
            geo_code=request.geo_code,
            interval=request.interval,
            start_date=request.start_date.strftime("%Y-%m-%d"),
            end_date=request.end_date.strftime("%Y-%m-%d"),
            task_id=None
        )
        
        # 查询数据库获取实际数据
        records = db.query(TimeInterest).filter(
            TimeInterest.id.in_(interest_ids)
        ).all()
        
        data = [
            {
                "geo_code": record.geo_code,
                "timeframe_start": record.timeframe_start,
                "timeframe_end": record.timeframe_end,
                "data": record.data
            }
            for record in records
        ]
        
        return TimeTrendsResponse(
            task_id=None,
            interest_ids=interest_ids,
            data=data
        )
    except Exception as e:
        raise HTTPException(500, str(e))