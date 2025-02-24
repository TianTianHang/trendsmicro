from typing import TypeVar
from fastapi import APIRouter, Depends, Query
from fastapi_pagination import Page, add_pagination
from fastapi_pagination.ext.sqlalchemy import paginate as sqlalchemy_paginate
from sqlalchemy.orm import Session
from api.dependencies.database import get_db
from api.schema.interest import RegionInterestSchema, TimeInterestSchema
from api.models.interest import RegionInterest,TimeInterest
from fastapi_pagination.customization import CustomizedPage, UseParamsFields
router = APIRouter(prefix="/interests")
T = TypeVar("T")

CustomPage = CustomizedPage[
    Page[T],
    UseParamsFields(
        size=Query(5, ge=1, le=1000, alias="pageSize"),
        page=Query(1, ge=1, alias="pageNumber"),
    ),
]
# 地区兴趣数据接口
@router.get("/region-interests", response_model=CustomPage[RegionInterestSchema])
async def get_region_interests(db: Session = Depends(get_db)):
    """使用分页插件获取地区兴趣数据"""
    query = db.query(
        RegionInterest
    )
    return sqlalchemy_paginate(query)

# 时间兴趣数据接口
@router.get("/time-interests", response_model=CustomPage[TimeInterestSchema])
async def get_time_interests(db: Session = Depends(get_db)):
    """使用分页插件获取时间兴趣数据"""
    query = db.query(
        TimeInterest
    )
    return sqlalchemy_paginate(query)

# 根据任务需求获取数据接口
@router.get("/task-interests", response_model=CustomPage[RegionInterestSchema])
async def get_task_interests(
    db: Session = Depends(get_db),
    start_time: str = Query(..., description="开始时间"),
    end_time: str = Query(..., description="结束时间"),
    keyword: str = Query(None, description="关键词")
):
    """根据任务需求获取数据"""
    query = db.query(RegionInterest).filter(
        RegionInterest.timestamp >= start_time,
        RegionInterest.timestamp <= end_time
    )
    if keyword:
        query = query.filter(RegionInterest.keyword.contains(keyword))
    return sqlalchemy_paginate(query)

add_pagination(router)
