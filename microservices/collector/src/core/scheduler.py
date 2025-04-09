#src/core/scheduler.py
import asyncio
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from fastapi.logger import logger
from sqlalchemy import create_engine
from api.dependencies.database import get_db
from api.models.tasks import HistoricalTask, ScheduledTask
from config import get_settings
from core.jobs import execute_historical_task, execute_scheduled_task
from api.dependencies.database import engine
from apscheduler.triggers.interval import IntervalTrigger

from core.dramatiq_manager import DramatiqManager
settings = get_settings()

class SchedulerManager:
    def __init__(self,dramatiq:DramatiqManager):
        self.scheduler = AsyncIOScheduler(
            jobstores={
            'default': SQLAlchemyJobStore(engine=engine)
            },
            timezone="Asia/Shanghai",
            job_defaults={
            'coalesce': False,
            'max_instances': 1
            },
            executors={
            'default': {'type': 'asyncio'}
            }
        )
        self.dramatiq=dramatiq
    
    def start(self):
        self.scheduler.start()
        
    def add_historical_job(self, task: HistoricalTask):
        """添加历史数据采集任务到调度器"""
        self.scheduler.add_job(
            id=f"historical_{task.id}",
            func=execute_historical_task,
            args=[task],
            trigger="date",  # 立即执行一次
            run_date=datetime.now() + timedelta(seconds=15),
            max_instances=1  # 只允许单个实例 
        )
        
    
    def add_cron_job(self, task: ScheduledTask):
        """添加定时任务到调度器并关联历史任务"""
        # 解析时间间隔配置
        interval_config = self._parse_interval(task.interval)
        
        self.scheduler.add_job(
            id=f"scheduled_{task.id}",
            func=self.dramatiq.add_cron_job,
            args=[task],
            trigger=IntervalTrigger(**interval_config, end_date=datetime.now() + timedelta(days=task.duration)),
            max_instances=2,  # 允许最大并发实例数
            misfire_grace_time=10  # 任务错过执行时间后的宽容时间
        )
        logger.info(f"interval_config: {interval_config}")
        
        
    def _parse_interval(self, interval):
        """解析时间间隔"""
        amount = int(interval[:-1])
        unit = interval[-1]
        if unit == 'h':
            return {'hours': amount}
        elif unit == 'd':
            return {'days': amount}
        elif unit == 'm':
            return {'minutes': amount}
        else:
            raise ValueError("Invalid interval format. Use 'h' for hours, 'd' for days, 'm' for minutes.")
   
   
    def remove_job(self, job_id: str):
        """移除任务"""
        self.scheduler.remove_job(job_id)
        
    def sync_job_status(self):
        """启动时同步调度器与应用表状态"""
        db = next(get_db())
        # 同步历史任务
        historical_tasks = db.query(HistoricalTask).all()
        for task in historical_tasks:
            if task and task.status == "waiting":
                task.status = "pending"  # 历史任务是一次性执行的
            if task and task.status == "running":
                task.status = "failed"  
        # 同步定时任务
        scheduled_tasks = db.query(ScheduledTask).all()
        for task in scheduled_tasks:
            job_id = f"scheduled_{task.id}"
            job = self.scheduler.get_job(job_id)
            task.enabled = job is not None and job.next_run_time is not None
        db.commit()
        db.close()
