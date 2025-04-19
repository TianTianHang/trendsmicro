from aio_pika import IncomingMessage
from fastapi.logger import logger
from sqlalchemy import update
from api.dependencies.database import get_db
from api.models.subject import Subject, SubjectData
from services.rabbitmq import RabbitMQClient
from services.collector import HistoricalTaskRequest, ScheduledTaskRequest
from fastapi_events.handlers.local import local_handler
from fastapi_events.typing import Event
import json

@local_handler.register(event_name="subject_create")
async def process_subject(event: Event):
    _, subject = event
    try:
        param = subject.parameters  # Union[RealtimeTask, HistoricalTask] 的数组
        # 解析参数
        for task_json in param:
            # 构造请求参数
            task = json.loads(task_json)
            req = None
            if task.get("type") == "realtime":
                req = ScheduledTaskRequest(
                    job_type=task.get("data_type"),
                    keywords=task.get("keywords"),
                    geo_code=task.get("geo_code"),
                    start_date=task.get("start_date"),
                    duration=task.get("duration"),
                    interval=task.get("interval")
                )
            elif task.get("type") == "historical":
                req = HistoricalTaskRequest(
                    job_type=task.get("data_type"),
                    keywords=task.get("keywords"),
                    geo_code=task.get("geo_code"),
                    start_date=task.get("start_date"),
                    end_date=task.get("end_date"),
                    interval=task.get("interval", None)
                )
            else:
                raise ValueError(f"Unknown task type: {task.get('type')}")

            # 发布消息到队列
            async with RabbitMQClient("collector_task_request") as client:
                await client.publish(message=req.model_dump_json(), properties=dict(delivery_mode=2,
                                                                              headers={"data_type":task.get("data_type"),
                                                                                       "subject_id":subject.subject_id}))
        db=next(get_db())
        db.execute(
                update(Subject)
                .where(Subject.subject_id == subject.subject_id)
                .values(status="processing", process=len(param))
        )
        db.commit()
    except ValueError as ve:
        logger.error(f"Invalid task parameters for subject {subject.subject_id}: {str(ve)}")
        db.rollback()
    except Exception as e:
        logger.error(f"Error processing subject {subject.subject_id}: {str(e)}")
        db.rollback()
        
        
@RabbitMQClient.consumer("collector_task_respone")        
async def process_collector_respone(message: IncomingMessage):
    async with message.process():
        result = json.loads(message.body)
        headers = message.headers
        db = next(get_db())
        if result.get("task_id",None)!=None:
            subjectData = SubjectData(
                data_type=headers.get("data_type"),
                subject_id=headers.get('subject_id'),
                task_id=result.get("task_id"),
            )
            db.add(subjectData)
        
            db.commit()
            logger.info(f"Successfully submitted task {headers.get('subject_id')} to collector")
        else:
            logger.error(f"Failed to submit task {headers.get('subject_id')},error:{result.get('error')}")
        db.close()