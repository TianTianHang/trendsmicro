from datetime import datetime
import json
from fastapi.logger import logger
from aio_pika import IncomingMessage
from sqlalchemy import update

from api.dependencies.database import get_db
from api.models.interest import InterestCollection
from api.schemas.subject import NotifyTimeRequest,NotifyRegionRequest
from api.models.subject import Subject, SubjectData
from services.rabbitmq import RabbitMQClient


@RabbitMQClient.consumer("interest_data")
async def handle_interest_data(message: IncomingMessage):
    """处理并保存历史数据"""
    json_req=json.loads(message.body.decode())
    if json_req.get('interest_type')=='time':
        req=NotifyTimeRequest(task_id=json_req.get('task_id'),
                  type=json_req.get('type'),
                  interest_type=json_req.get('interest_type'),
                  interests=[[{**j, 'time [UTC]': datetime.fromtimestamp(float(j.get('time [UTC]'))/1000).strftime("%Y-%m-%d %H:%M:%S")} for j in json.loads(i)]
                             for i in json_req.get('interests',[])],
                  meta=[json.loads(i) for i in json_req.get('meta',[])]
                  )
    else:
        req=NotifyRegionRequest(task_id=json_req.get('task_id'),
                      type=json_req.get('type'),
                      interest_type=json_req.get('interest_type'),
                      interests=[json.loads(i) for i in json_req.get('interests',[])],
                      meta=[json.loads(i) for i in json_req.get('meta',[])]
                      )
    db = next(get_db())
    
    try:
        
        subjectData = db.query(SubjectData).filter(SubjectData.task_id == req.task_id,
                                                   SubjectData.data_type == req.type
                                                   ).first()
        if not subjectData:
            logger.warning(f"SubjectData with task_id {req.task_id} not found")
        # 先创建meta data
        meta_instances = [m.convert(subjectData.id if subjectData else None) for m in req.meta]
        db.add_all(meta_instances)
        db.commit()
        
        # 为每个collection创建interest collection并关联meta data
        for index, collection in enumerate(req.interests):
            ic = InterestCollection(
                interest_type=req.interest_type,
                subject_data_id=subjectData.id if subjectData else None,
                meta_data_id=meta_instances[index].id if meta_instances else None
            )
            db.add(ic)
            db.commit()
            db.refresh(ic)
            db.add_all([i.convert(ic.id) for i in collection])
        logger.info(f"任务 {req.task_id} 的数据已成功保存")
        if subjectData:
            subject = db.query(Subject).filter(Subject.subject_id == subjectData.subject_id).first()
            subject.process -= 1
            db.commit()
            db.refresh(subject)
            if subject.process == 0:
                db.execute(
                update(Subject)
                .where(Subject.subject_id == subject.subject_id)
                .values(status="completed")
                )
            logger.info(f"Subject {subject.subject_id} has been completed")
        db.commit()
        
        await message.ack()
    except Exception as e:
        db.rollback()
        logger.error(f"保存任务 {req.task_id} 的数据失败: {str(e)}")
        raise
    finally:
        db.close()