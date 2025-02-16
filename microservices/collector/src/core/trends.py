#src/core/trends.py
from datetime import datetime
import time
from fastapi.logger import logger
from requests import HTTPError
from sqlalchemy.exc import IntegrityError
from trendspy import Trends
from api.dependencies.database import get_db
from api.models.interest import RegionInterest, TimeInterest
from config import get_settings
from core.utils.time_splitter import split_time_ranges
from api.models.tasks import RequestHistory

def _call_trends_api_with_retry(api_call_func, max_retries=3,**kwargs):
    """封装API调用，包含速率限制处理和重试机制"""
    retries = 0
    while retries < max_retries:
        try:    
            response = api_call_func(**kwargs)
            logger.info(
                f"Data fetch successful for API function: {api_call_func.__name__}, "
                f"with parameters - Keywords: {kwargs.get('keywords')}, "
                f"Timeframe: {kwargs.get('timeframe')}, "
                f"Geo: {kwargs.get('geo')}"
            )
            return response
        except HTTPError as e:
            if e.response.status_code == 429:  # 速率限制错误
                retry_after = int(e.response.headers.get('Retry-After', 60))  # 默认等待60秒
                logger.warning(f"Rate limited. Retrying after {retry_after} seconds...")
                time.sleep(retry_after)
                retries += 1
            else:
                raise
    
    raise Exception("Max retries exceeded for API call")

settings = get_settings()
trends=Trends(
        request_delay=settings.request_delay,
       proxies = {
            'http': settings.proxy,
            'https': settings.proxy
        }
    )

def get_interest_by_region(keyword: str, geo_code: str, interval: str, start_date: str, end_date: str):
    db=next(get_db())
    time_ranges = split_time_ranges(start_date, end_date, interval)
    

    for start, end in time_ranges:
        # 检查请求历史表判断是否已处理
        timeframe_start = datetime.strptime(start, "%Y-%m-%d").date()
        timeframe_end = datetime.strptime(end, "%Y-%m-%d").date()
        
        # 查询请求历史表
        history = db.query(RequestHistory).filter(
            RequestHistory.job_type == "region",
            RequestHistory.keyword == keyword,
            RequestHistory.geo_code == geo_code,
            RequestHistory.timeframe_start == timeframe_start,
            RequestHistory.timeframe_end == timeframe_end
        ).first()
        
        if history and history.status=="success":
            continue  # 跳过已处理的请求
        elif not history:
            try:
                history = RequestHistory(
                        job_type = "region",
                        keyword=keyword,
                        geo_code=geo_code,
                        timeframe_start=timeframe_start,
                        timeframe_end=timeframe_end,
                        )
                db.add(history)
                db.commit()
            except IntegrityError as e:
                db.rollback()
                logger.error(f"数据已存在或冲突: {str(e)}")
                raise 
        try:
            # 调用API获取数据
            timeframe = f"{start} {end}"
            region_data = _call_trends_api_with_retry(
                trends.interest_by_region, max_retries=3,keywords=keyword,geo=geo_code, timeframe=timeframe, inc_low_vol=True
            )
            
            # 使用事务保证数据一致性
            with db.begin_nested():
                # 存储区域兴趣数据
                for _, row in region_data.iterrows():
                    record = RegionInterest(
                        keyword=keyword,
                        geo_code=row["geoCode"],
                        timeframe_start=timeframe_start,
                        timeframe_end=timeframe_end,
                        value=row[keyword]
                    )   
                    db.add(record)
                
                # 记录请求历史
                history.status="success"
                db.commit()
            
        except IntegrityError as e:
            db.rollback()
            logger.error(f"数据已存在或冲突: {str(e)}")
            history.status="failed"
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Error: {str(e)}")
            history.status="failed"
            db.commit()
            
            
def get_interest_over_time(keyword: str, geo_code: str, interval: str, start_date: str, end_date: str):
    db=next(get_db())
    time_ranges = split_time_ranges(start_date, end_date, interval)
   

    for start, end in time_ranges:
        # 检查是否已存在数据
        exists = db.query(TimeInterest).filter(
            TimeInterest.keyword == keyword,
            TimeInterest.geo_code == geo_code,
            TimeInterest.time >= datetime.strptime(start,"%Y-%m-%d %H:%M:%S"),
            TimeInterest.time <= datetime.strptime(end,"%Y-%m-%d %H:%M:%S")
        ).first()
        
        if exists:
            continue

        # 调用API获取数据
        timeframe = f"{start} {end}"
        try:
            # 封装API调用并添加速率控制
            time_data = _call_trends_api_with_retry(
                trends.interest_over_time,max_retries=3,keywords=keyword, geo=geo_code, timeframe=timeframe
            )
            # 存储到数据库
            for date, row in time_data.iterrows():
                record = TimeInterest(
                    keyword=keyword,
                    geo_code=geo_code,
                    time=datetime.strptime(end,"%Y-%m-%d %H:%M:%S"),
                    value=row[keyword],
                    is_partial=row["isPartial"]
                )
                db.add(record)
            db.commit()
        except IntegrityError:
            db.rollback()
            raise IntegrityError
        except Exception as e:
            print(f"Error fetching/saving data for {keyword} ({geo_code}): {str(e)}")
            db.rollback()