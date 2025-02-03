#src/core/trends.py
from datetime import datetime
import time
from requests import HTTPError
from sqlalchemy.exc import IntegrityError
from trendspy import Trends
from api.dependencies.database import get_db
from api.models.interest import RegionInterest, TimeInterest
from config import get_settings
from core.utils.time_splitter import split_time_ranges
def _call_trends_api_with_retry(api_call_func, max_retries=3):
    """封装API调用，包含速率限制处理和重试机制"""
    retries = 0
    while retries < max_retries:
        try:
            # 固定延迟（使用配置参数）
            if settings.request_delay > 0:
                time.sleep(settings.request_delay)
                
            response = api_call_func()
            return response
        except HTTPError as e:
            if e.response.status_code == 429:  # 速率限制错误
                retry_after = int(e.response.headers.get('Retry-After', 60))  # 默认等待60秒
                print(f"Rate limited. Retrying after {retry_after} seconds...")
                time.sleep(retry_after)
                retries += 1
            else:
                raise
    raise Exception("Max retries exceeded for API call")

settings = get_settings()
trends=Trends(
        request_delay=settings.request_delay,
        proxy=settings.proxy
    )
def get_interest_by_region(keyword: str, geo_code: str, interval: str, start_date: str, end_date: str):
    time_ranges = split_time_ranges(start_date, end_date, interval)
    db = next(get_db())

    for start, end in time_ranges:
        # 检查是否已存在数据
        exists = db.query(RegionInterest).filter(
            RegionInterest.keyword == keyword,
            RegionInterest.timeframe_start == datetime.strptime(start,"%Y-%m-%d"),
            RegionInterest.timeframe_end == datetime.strptime(end,"%Y-%m-%d")
        ).first()
        
        if exists:
            continue  # 跳过已存在的数据

        # 调用API获取数据
        timeframe = f"{start} {end}"
        try:
            # 封装API调用并添加速率控制
            region_data = _call_trends_api_with_retry(
                lambda: trends.interest_by_region(keyword, geo=geo_code, timeframe=timeframe, inc_low_vol=True)
            )
            # 存储到数据库
        
            for _, row in region_data.iterrows():
                record = RegionInterest(
                    keyword=keyword,
                    geo_code=row["geoCode"],
                    timeframe_start=datetime.strptime(start,"%Y-%m-%d"),
                    timeframe_end=datetime.strptime(end,"%Y-%m-%d"),
                    value=row[keyword]  # 假设API返回的列名与keyword一致
                )   
                db.add(record)        
            db.commit()
        except IntegrityError:
            db.rollback()
            raise IntegrityError
        except Exception as e:
            print(f"Error fetching/saving data for {keyword} ({geo_code}): {str(e)}")
            db.rollback()
            raise e

    db.close()

def get_interest_over_time(keyword: str, geo_code: str, interval: str, start_date: str, end_date: str):
    time_ranges = split_time_ranges(start_date, end_date, interval)
    db = next(get_db())

    for start, end in time_ranges:
        # 检查是否已存在数据
        exists = db.query(TimeInterest).filter(
            TimeInterest.keyword == keyword,
            TimeInterest.geo_code == geo_code,
            TimeInterest.time >= datetime.strptime(start,"%Y-%m-%d"),
            TimeInterest.time <= datetime.strptime(end,"%Y-%m-%d")
        ).first()
        
        if exists:
            continue

        # 调用API获取数据
        timeframe = f"{start} {end}"
        try:
            # 封装API调用并添加速率控制
            time_data = _call_trends_api_with_retry(
                lambda: trends.interest_over_time(keyword, geo=geo_code, timeframe=timeframe)
            )
            # 存储到数据库
            for date, row in time_data.iterrows():
                record = TimeInterest(
                    keyword=keyword,
                    geo_code=geo_code,
                    time=datetime.strptime(date,"%Y-%m-%d"),
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
            raise e
    db.close()