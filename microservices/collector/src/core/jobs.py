# src/core/jobs.py
from datetime import datetime, timedelta
from fastapi.logger import logger
import dramatiq
from api.dependencies.database import get_db
from api.models.tasks import HistoricalTask, ScheduledTask
from core.trends import get_interest_by_region, get_interest_over_time
from fastapi_events.dispatcher import dispatch

async def execute_task(job_type, keywords, geo_code, interval, start_date, end_date,task_id):
    """通用任务执行函数"""
    # 根据任务类型调用对应的趋势函数
    logger.info("开始采集数据")
    if job_type == "region":
        last_id= get_interest_by_region(keywords, geo_code, interval, start_date, end_date,task_id)
    elif job_type == "time":
        last_id= get_interest_over_time(keywords, geo_code, interval, start_date, end_date,task_id)
    else:
        raise ValueError(f"无效的任务类型: {job_type}")
    logger.info("采集数据结束")
    return last_id
@dramatiq.actor
async def execute_historical_task(task:HistoricalTask):
    """执行历史数据采集任务"""
    db = next(get_db())
    try:
        # 更新状态为running
        db_task = db.query(HistoricalTask).get(task.id)
        if db_task:
            db_task.status = "running"
            db.commit()
        if task.geo_code=="World":
            task.geo_code=""
        # 执行任务
        interest_id=execute_task(
            task.job_type, task.keywords, task.geo_code, 
            task.interval, task.start_date, task.end_date,
            task.id
        )
        
        # 更新状态为completed
        db_task = db.query(HistoricalTask).get(task.id)
        if db_task:
            db_task.status = "completed"
            db.commit()
            dispatch(event_name="historical_task_finish",
                     payload={
                            "task_id": db_task.schedule_id if db_task.schedule_id else db_task.id,
                            "interest_type": db_task.job_type,
                            "type": "realtime" if db_task.schedule_id else "historical",
                            "interest_id":interest_id
                         },middleware_id=8888)
    except Exception as e:
        # 更新状态为failed
        db_task = db.query(HistoricalTask).get(task.id)
        if db_task:
            db_task.status = "failed"
            db.commit()
        raise e  # 重新抛出异常以便APScheduler记录日志
    finally:
        db.close()
        
@dramatiq.actor
async def execute_scheduled_task(task:ScheduledTask):
    """执行定时数据采集任务并生成历史任务记录"""
    db = next(get_db())
    try:
        # 创建关联的历史任务
        historical_task = HistoricalTask(
            job_type=task.job_type,
            keywords=task.keywords,
            geo_code=task.geo_code,
            start_date=task.start_date.strftime("%Y-%m-%d"),
            end_date=datetime.now().strftime("%Y-%m-%d"),
            interval=None,
            schedule_id=task.id,
            status='pending'
        )
        if task.job_type=='region':
            interval=task.interval
            amount = int(interval[:-1])
            unit = interval[-1]
            if unit == 'h':
                start_date=datetime.now()-timedelta(hours=amount)
            elif unit == 'd':
                start_date=datetime.now()-timedelta(days=amount)
            elif unit == 'm':
                start_date=datetime.now()-timedelta(minutes=amount)
            historical_task = HistoricalTask(
            job_type=task.job_type,
            keywords=task.keywords,
            geo_code=task.geo_code,
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=datetime.now().strftime("%Y-%m-%d"),
            interval=None,
            schedule_id=task.id,
            status='pending'
        )
        db.add(historical_task)
        db.commit()
        db.refresh(historical_task)
        dispatch(event_name="historical_task_create",payload=historical_task,middleware_id=8888)
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()