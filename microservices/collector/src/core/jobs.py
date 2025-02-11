# src/core/jobs.py
from datetime import date, datetime
from sqlalchemy.orm import Session
from fastapi import Depends
from fastapi.logger import logger
from api.dependencies.database import get_db
from api.models.tasks import HistoricalTask, ScheduledTask
from core.trends import get_interest_by_region, get_interest_over_time
from core.utils.time_interval import parse_interval

def execute_task(job_type,keyword, geo_code, interval,start_date,end_date):
    """通用任务执行函数"""
    # 根据任务类型调用对应的趋势函数
    logger.info("开始采集数据")
    if job_type == "region":
        get_interest_by_region(keyword, geo_code, interval, start_date, end_date)
    elif job_type == "time":
        get_interest_over_time(keyword, geo_code, interval, start_date, end_date)
    else:
        raise ValueError(f"无效的任务类型: {job_type}")
    logger.info("采集数据结束")
    
    
def execute_historical_task(task:HistoricalTask):
    """执行历史数据采集任务"""
    db=next(get_db())
    try:
        # 更新状态为running
        db_task = db.query(HistoricalTask).get(task.id)
        if db_task:
            db_task.status = "running"
            db.commit()
        
        # 执行任务
        execute_task(
            task.job_type, task.keyword, task.geo_code, 
            task.interval, task.start_date, task.end_date
        )
        
        # 更新状态为completed
        db_task = db.query(HistoricalTask).get(task.id)
        if db_task:
            db_task.status = "completed"
            db.commit()
    except Exception as e:
        # 更新状态为failed
        db_task = db.query(HistoricalTask).get(task.id)
        if db_task:
            db_task.status = "failed"
            db.commit()
        raise e  # 重新抛出异常以便APScheduler记录日志

def execute_scheduled_task(task:ScheduledTask):
    """执行定时数据采集任务"""
    end_date = date.now().strftime("%Y-%m-%d %H:%M:%S")
    start_date = (date.now() - parse_interval(task.interval)).strftime("%Y-%m-%d %H:%M:%S")
    execute_task(task.job_type,task.keyword, task.geo_code, None,start_date,end_date)