from fastapi.logger import logger
from api.dependencies.database import get_db
from fastapi_events.typing import Event
from fastapi_events.handlers.local import local_handler
from core import scheduler_manager
from api.models.interest import RegionInterest, TimeInterest
from api.schema.interest import InterestMetaData
from services import query
from services.query import NotifyRequest
@local_handler.register(event_name="historical_task_create")
async def handle_pending_tasks(event: Event):
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

@local_handler.register(event_name="historical_task_finish")
async def handle_finish_tasks(event: Event):
    _,task=event
    db=next(get_db())
    interest_type = task.get("interest_type")
    interest_id = task.get("interest_id")
    
    if interest_type == "time":
        interest = db.query(TimeInterest).filter(TimeInterest.id.in_(interest_id))
    elif interest_type == "region":
        interest = db.query(RegionInterest).filter(RegionInterest.id.in_(interest_id))
    
    interests = interest.all()
    
    req = NotifyRequest(
        task_id=task.get("task_id"),
        type=task.get("type"),
        interest_type=interest_type,
        interests=[r.data for r in interests],
        meta=[InterestMetaData(
                geo_code=r.geo_code,
                keywords=r.keywords,
                timeframe_start=r.timeframe_start,
                timeframe_end=r.timeframe_end
            ) for r in interests]
    )
    await query.task_finish(req)