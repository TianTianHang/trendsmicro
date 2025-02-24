from datetime import datetime
from fastapi import Depends
from fastapi.logger import logger
import httpx
from sqlalchemy import update
from sqlalchemy.orm import Session
from api.dependencies.database import get_db
from api.models.subject import Subject
from services.collector import HistoricalTaskRequest, ScheduledTaskRequest
from fastapi_events.handlers.local import local_handler
from fastapi_events.typing import Event
from services import collector
import json
@local_handler.register(event_name="subject_create")
async def process_subject(event: Event):
       
        _, subject = event
        try:
            param = subject.parameters  # Union[RealtimeTask, HistoricalTask] 的数组
            # 解析参数
            for task_json in param:
                # 构造请求参数
                task=json.loads(task_json)
                if task.get("type") == "realtime":
                    req = ScheduledTaskRequest(
                    job_type=task.get("data_type"),
                    keywords=task.get("keywords"),
                    geo_code=task.get("geo_code"),
                    start_date=datetime.strptime(task.get("start_date"),"%Y-%m-%dT%H:%M:%S"),
                    duration=task.get("duration"),
                    interval=task.get("interval")
                )
                elif task.get("type") == "historical":
                    req = HistoricalTaskRequest(
                    job_type=task.get("data_type"),
                    keywords=task.get("keywords"),
                    geo_code=task.get("geo_code"),
                    start_date=datetime.strptime(task.get("start_date"),"%Y-%m-%dT%H:%M:%S"),
                    end_date=datetime.strptime(task.get("end_date"),"%Y-%m-%dT%H:%M:%S"),
                    interval=task.get("interval")
                )
                else:
                    raise ValueError(f"Unknown task type: {task.get('type')}")
           
                # 调用collector服务
                result = await collector.add_task(req)
                db=next(get_db())
                if result:
                    # 更新任务状态
                    db.execute(
                        update(Subject)
                        .where(Subject.subject_id == subject.subject_id)
                        .values(status="processing", collector_task_id=result.get("task_id"))
                    )
                    logger.info(f"Successfully submitted task {subject.subject_id} to collector")
                else:
                    logger.error(f"Failed to submit task {subject.subject_id}")

        except ValueError as ve:
            logger.error(f"Invalid task parameters for subject {subject.subject_id}: {str(ve)}")
        except httpx.HTTPError as he:
            logger.error(f"HTTP error submitting task {subject.subject_id}: {str(he)}")
        except Exception as e:
            logger.error(f"Error processing subject {subject.subject_id}: {str(e)}")