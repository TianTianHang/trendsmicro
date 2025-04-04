from datetime import datetime
import json
from aio_pika import IncomingMessage
from fastapi.logger import logger
from api.dependencies.database import get_db
from fastapi_events.typing import Event
from fastapi_events.handlers.local import local_handler
from core import scheduler_manager
from api.models.interest import RegionInterest, TimeInterest
from api.schemas.interest import InterestMetaData
from api.schemas.tasks import HistoricalTaskRequest, ScheduledTaskRequest
from api.models.tasks import HistoricalTask, ScheduledTask
from services.rabbitmq import RabbitMQClient
from fastapi_events.dispatcher import dispatch
@local_handler.register(event_name="historical_task_create")
async def handle_pending_tasks(event: Event):
        """调度未执行的历史任务"""
        db = next(get_db())
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
        finally:
            db.close()
@local_handler.register(event_name="historical_task_finish")
async def handle_finish_tasks(event: Event):
    _,task=event
    db = next(get_db())
    
    interest_type = task.get("interest_type")
    
    interest_id = task.get("interest_id")
    
    if interest_type == "time":
        interest = db.query(TimeInterest).filter(TimeInterest.id.in_(interest_id))
    elif interest_type == "region":
        interest = db.query(RegionInterest).filter(RegionInterest.id.in_(interest_id))
    
    interests = interest.all()
   
    req = dict(
        task_id=task.get("task_id"),
        type=task.get("type"),
        interest_type=interest_type,
        interests=[r.data for r in interests],
        meta=[InterestMetaData(
                geo_code=r.geo_code,
                keywords=r.keywords,
                timeframe_start=r.timeframe_start,
                timeframe_end=r.timeframe_end
            ).model_dump_json() for r in interests]
    )
    # 通过队列通知query 服务保存数据
    async with RabbitMQClient("interest_data") as client:
        await client.publish(json.dumps(req),properties=dict(delivery_mode=2))
    db.close()      
        
@RabbitMQClient.consumer("collector_task_request")
async def subject_task_request(message: IncomingMessage):
    async with message.process():
        try:
            task_req = json.loads(message.body)
            db = next(get_db())
            
            if task_req.get("duration",None)!=None:
                task_req=ScheduledTaskRequest.model_validate(task_req)
                task = ScheduledTask(**task_req.model_dump())
                db.add(task)
                db.commit()
                db.refresh(task)
                # 添加到调度器
                scheduler_manager.add_cron_job(task)
            #HistoricalTaskRequest
            elif task_req.get("end_date",None)!=None:
                task_req=HistoricalTaskRequest.model_validate(task_req)
                # 保存任务到数据库
                task = HistoricalTask(**task_req.model_dump())
                db.add(task)
                db.commit()
                db.refresh(task)
                db.close()
                dispatch(event_name="historical_task_create",payload=task,middleware_id=8888)
            async with RabbitMQClient("collector_task_respone") as client:
                await client.publish(message=json.dumps({"task_id":task.id}),properties=dict(delivery_mode=2,
                                                                                       headers=message.headers))
        except Exception as e:
            logger.error(f"Failed to process message: {str(e)}")
            async with RabbitMQClient("collector_task_respone") as client:
                await client.publish(message=json.dumps({"error":str(e)}),properties=dict(delivery_mode=2,
                                                                                    headers=message.headers))
        finally:
            db.close()