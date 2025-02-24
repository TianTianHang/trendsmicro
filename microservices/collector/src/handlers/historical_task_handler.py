from fastapi import Depends
from fastapi.logger import logger
from api.dependencies.database import get_db
from sqlalchemy.orm import Session
from fastapi_events.typing import Event
from api.models.tasks import HistoricalTask
from fastapi_events.handlers.local import local_handler
from core import scheduler_manager

@local_handler.register(event_name="historical_task_create")
def handle_pending_tasks(event: Event):
        """调度未执行的历史任务"""
        db=next(get_db())
        _,task=event
        try:
            # 将任务加入调度队列
            scheduler_manager.add_historical_job(task)
            
            # 更新任务状态为waiting
            task.status = "waiting"
            db.commit()
            logger.info(f"任务 {task.id} 已加入队列等待执行")
            
        except Exception as e:
            db.rollback()
            logger.error(f"任务 {task.id} 加入队列失败: {str(e)}")

@local_handler.register(event_name="historical_task_finsh")
def handle_finish_tasks(event: Event):
    _,task=event
    query.task_finish(task)
    pass