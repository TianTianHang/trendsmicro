#src/core/scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from sqlalchemy import create_engine
from api.dependencies.database import get_db
from api.models.tasks import HistoricalTask, ScheduledTask
from config import get_settings
from core.jobs import execute_historical_task, execute_scheduled_task

settings = get_settings()

class SchedulerManager:
    def __init__(self):
        self.scheduler = BackgroundScheduler(
            jobstores={
                'default': SQLAlchemyJobStore(engine=create_engine(settings.database_url))
            },
            timezone="UTC"
        )
    
    def start(self):
        self.scheduler.start()
    
    def add_historical_job(self, task: HistoricalTask):
        """添加历史数据采集任务到调度器"""
        self.scheduler.add_job(
            id=f"historical_{task.id}",
            func=execute_historical_task,
            args=[task],
            trigger="date",  # 立即执行一次
        )
        
    
    def add_cron_job(self, task: ScheduledTask):
        """添加定时任务到调度器"""
        self.scheduler.add_job(
            id=f"scheduled_{task.id}",
            func=execute_scheduled_task,
            args=[task],
            trigger="cron",
            **self.parse_cron(task.cron_expression)
        )
    
    def parse_cron(self, cron_exp: str) -> dict:
        parts = cron_exp.split()
        return {
            "minute": parts[0],
            "hour": parts[1],
            "day": parts[2],
            "month": parts[3],
            "day_of_week": parts[4]
        }
    def remove_job(self, job_id: str):
        """移除任务"""
        self.scheduler.remove_job(job_id)
    def sync_job_status(self):
        """启动时同步调度器与应用表状态"""
        db = next(get_db())
        # 同步历史任务
        for job in self.scheduler.get_jobs():
            if job.id.startswith("historical_"):
                task_id = int(job.id.split("_")[1])
                task = db.query(HistoricalTask).get(task_id)
            if task and task.status == "pending":
                task.status = "completed"  # 历史任务是一次性执行的
            if task and task.status == "running":
                task.status = "failed"  
        # 同步定时任务
        scheduled_tasks = db.query(ScheduledTask).all()
        for task in scheduled_tasks:
            job_id = f"scheduled_{task.id}"
            job = self.scheduler.get_job(job_id)
            task.enabled = job is not None and job.next_run_time is not None
        db.commit()