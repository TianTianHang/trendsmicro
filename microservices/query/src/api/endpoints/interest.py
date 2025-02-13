from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
import pandas as pd
from sqlalchemy import and_, asc, desc
from sqlalchemy.orm import Session
from api.models.interest import RegionInterest
from api.dependencies.database import OPERATOR_MAP, get_db
from api.models.interest import TimeInterest
from api.schemas.interest import RegionInterestRespone, TimeInterestResponse
from api.schemas.query import QueryParams
router = APIRouter(prefix="/interest")


@router.post("/region-interests", response_model=List[RegionInterestRespone])
def query_region_interest(
    query_params: QueryParams,
    db: Session = Depends(get_db)
):
    query = db.query(RegionInterest)

    # 处理过滤条件
    if query_params.filters:
        filters = []
        for filter in query_params.filters:
            field = getattr(RegionInterest, filter.field, None)
            if not field:
                raise HTTPException(status_code=400, detail=f"Invalid field: {filter.field}")
            op_func = OPERATOR_MAP.get(filter.op)
            if not op_func:
                raise HTTPException(status_code=400, detail=f"Invalid operator: {filter.op}")
            filters.append(op_func(field, filter.value))
        if filters:
            query = query.filter(and_(*filters))

    # 处理排序
    if query_params.sorts:
        for sort in query_params.sorts:
            field = getattr(RegionInterest, sort.field, None)
            if not field:
                raise HTTPException(status_code=400, detail=f"Invalid field: {sort.field}")
            if sort.order == "desc":
                query = query.order_by(desc(field))
            else:
                query = query.order_by(asc(field))

    # 分页查询
    if query_params.limit==-1:
        results = query.all()
    else:
        results = query.offset(query_params.skip).limit(query_params.limit).all()
    return results





@router.post("/time-interests", response_model=List[TimeInterestResponse])
def query_time_interest_response(
    query_params: QueryParams,
    db: Session = Depends(get_db)
):
    query = db.query(TimeInterestResponse)

    # 处理过滤条件
    if query_params.filters:
        filters = []
        for filter in query_params.filters:
            field = getattr(TimeInterestResponse, filter.field, None)
            if not field:
                raise HTTPException(status_code=400, detail=f"Invalid field: {filter.field}")
            op_func = OPERATOR_MAP.get(filter.op)
            if not op_func:
                raise HTTPException(status_code=400, detail=f"Invalid operator: {filter.op}")
            filters.append(op_func(field, filter.value))
        if filters:
            query = query.filter(and_(*filters))

    # 处理排序
    if query_params.sorts:
        for sort in query_params.sorts:
            field = getattr(TimeInterestResponse, sort.field, None)
            if not field:
                raise HTTPException(status_code=400, detail=f"Invalid field: {sort.field}")
            if sort.order == "desc":
                query = query.order_by(desc(field))
            else:
                query = query.order_by(asc(field))

    # 分页查询
    results = query.offset(query_params.skip).limit(query_params.limit).all()
    return results




@router.post("/region_interest/import")
async def import_region_interest(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    file_name = file.filename.split(".")[0]  # 去掉文件扩展名
    parts = file_name.split('-')
    try:
        # 将 timeframe_start 和 timeframe_end 转换为日期对象
        try:
            start_date = datetime.strptime("-".join(parts[1:4]), "%Y-%m-%d").date()
            end_date = datetime.strptime("-".join(parts[4:]), "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Expected YYYY-MM-DD")
        keyword=parts[0]
        # 读取 CSV 文件
        df = pd.read_csv(file.file)
        file.file.close()

        # 检查 CSV 文件是否包含必要的字段
        required_columns = {"geoCode", keyword}
        if not required_columns.issubset(df.columns):
            raise HTTPException(
                status_code=400,
                detail=f"CSV file must contain the following columns: {required_columns}"
            )

        # 将数据转换为模型对象
        for _, row in df.iterrows():
            try:
                region_interest = RegionInterest(
                    keyword=keyword,
                    geo_code=row["geoCode"],
                    timeframe_start=start_date,
                    timeframe_end=end_date,
                    value=row[keyword]
                )
                db.add(region_interest)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Error processing row {row}: {str(e)}")

        # 提交到数据库
        db.commit()
        return {"message": f"Successfully imported {len(df)} rows into RegionInterest"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error importing data: {str(e)}")

@router.post("/time_interest/import")
async def import_time_interest(file: UploadFile = File(...), 
                               db: Session = Depends(get_db)):
    file_name = file.filename.split(".")[0]  # 去掉文件扩展名
    parts = file_name.split('-')
    geo_code=parts[0]
    keyword=parts[1]
    try:
        # 读取 CSV 文件
        df = pd.read_csv(file.file)
        file.file.close()
         # 检查 CSV 文件是否包含必要的字段
        required_columns = {"time [UTC]",keyword,"isPartial"}
        if not required_columns.issubset(df.columns):
            raise HTTPException(
                status_code=400,
                detail=f"CSV file must contain the following columns: {required_columns}"
            )
        # 将数据转换为模型对象
        for _, row in df.iterrows():
            try:
                time = datetime.strptime(row["time [UTC]"], "%Y-%m-%d").date() if pd.notna(row["time [UTC]"]) else None

                time_interest = TimeInterest(
                    keyword=keyword,
                    geo_code=geo_code,
                    time=time,
                    value=row[keyword],
                    is_partial=bool(row["isPartial"]) if pd.notna(row["isPartial"]) else None
                )
                db.add(time_interest)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Error processing row {row}: {str(e)}")

        # 提交到数据库
        db.commit()
        return {"message": f"Successfully imported {len(df)} rows into TimeInterestResponse"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error importing data: {str(e)}")