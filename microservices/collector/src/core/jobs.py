# src/core/jobs.py
from datetime import datetime, timedelta
import json
from sqlalchemy import inspect
import dramatiq
from api.dependencies.database import get_db
from api.models.tasks import HistoricalTask, ScheduledTask
from core.trends import get_interest_by_region, get_interest_over_time
import dramatiq
from dramatiq.brokers.rabbitmq import RabbitmqBroker
from config import get_settings
from dramatiq.middleware.asyncio import AsyncIO
from dramatiq.middleware import Retries

import logging

# 配置基本的日志设置
logging.basicConfig(
    level=logging.INFO,  # 设置最低显示的日志级别
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # 日志格式
    handlers=[
        logging.StreamHandler(),  # 输出到控制台
        logging.FileHandler('dramatiq_tasks.log')  # 输出到文件
    ]
)
    
logger = logging.getLogger('DramatiqTasks')
settings = get_settings()

rabbitmq_broker = RabbitmqBroker(
    url=f"amqp://{settings.rabbitmq_username}:{settings.rabbitmq_username}@{settings.rabbitmq_host}:{settings.rabbitmq_port}",
   middleware=[AsyncIO(),Retries(max_retries=3, min_backoff=60000, max_backoff=360000)]
)


dramatiq.set_broker(rabbitmq_broker)


def execute_task(job_type, keywords, geo_code, interval, start_date, end_date,task_id):
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
@dramatiq.actor(retry_when=lambda x,y: True)
async def execute_historical_task(job_type, keywords, geo_code, interval, start_date, end_date,id,**kwargs):
    """执行历史数据采集任务"""
   
    try:
        # 更新状态为running
        db = next(get_db())
        db_task = db.query(HistoricalTask).get(id)
        if db_task:
            db_task.status = "running"
            db.commit()
            db.close()
        if geo_code=="World":
            geo_code=""
        # 执行任务
        interest_id=execute_task(
            job_type, keywords, geo_code, 
            interval, start_date, end_date,
            id
        )
        
        # 更新状态为completed
        db_task = db.query(HistoricalTask).get(id)
        if db_task:
            db_task.status = "completed"
            db.commit()
            kwargs={
                        "task_id": db_task.schedule_id if db_task.schedule_id else db_task.id,
                        "interest_type": db_task.job_type,
                        "type": "realtime" if db_task.schedule_id else "historical",
                        "interest_id":interest_id
                    }
            db.close()
            await handle_finish_tasks(kwargs)
            
            
    except Exception as e:
        # 更新状态为failed
        db.close()
        db = next(get_db())
        db_task = db.query(HistoricalTask).get(id)
        if db_task:
            db_task.status = "failed"
            db.commit()
        raise e  # 重新抛出异常以便APScheduler记录日志
    finally:
        db.close()
        
@dramatiq.actor(retry_when=lambda x,y: True)
def execute_scheduled_task(job_type, keywords, geo_code, interval, start_date, id, duration=None, created_at=None, **kwargs):
    """执行定时数据采集任务并生成历史任务记录"""
    # 首次执行时记录创建时间
    current_time = datetime.now()
    if created_at is None:
        created_at = current_time
    else:
        created_at = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
    
    # 检查是否超过duration限制
    if duration and (current_time - created_at).days >= duration:
        return

    db = next(get_db())
    try:
        # 创建关联的历史任务
        historical_task = HistoricalTask(
            job_type=job_type,
            keywords=keywords,
            geo_code=geo_code,
            start_date=datetime.strptime(start_date,"%Y-%m-%d"),
            end_date=current_time.strftime("%Y-%m-%d"),
            interval=None,
            schedule_id=id,
            status='pending'
        )
        amount = int(interval[:-1])
        unit = interval[-1]
        if job_type == 'region':
           
            if unit == 'h':
                start_date = current_time - timedelta(hours=amount)
            elif unit == 'd':
                start_date = current_time - timedelta(days=amount)
            elif unit == 'm':
                start_date = current_time - timedelta(minutes=amount)
                
            historical_task.start_date = start_date.strftime("%Y-%m-%d")

        db.add(historical_task)
        db.commit()
        db.refresh(historical_task)
        handle_pending_tasks(historical_task)
        
        # 重新调度自己
        execute_scheduled_task.send_with_options(
            kwargs={
                'job_type': job_type,
                'keywords': keywords,
                'geo_code': geo_code,
                'interval': interval,
                'start_date': start_date,
                'id': id,
                'duration': duration,
                'created_at': created_at.strftime("%Y-%m-%d %H:%M:%S")
            },
            delay=timedelta(**{
                'hours': amount if unit == 'h' else 0,
                'days': amount if unit == 'd' else 0,
                'minutes': amount if unit == 'm' else 0
            }).total_seconds() * 1000
        )
        
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()




def handle_pending_tasks(task:HistoricalTask):
        """调度未执行的历史任务"""
        db = next(get_db())
    
        try:
            # 将任务加入调度队列
            from core import scheduler_manager 

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



async def handle_finish_tasks(task):
    from services.rabbitmq import RabbitMQClient
    from api.models.interest import RegionInterest, TimeInterest
    from api.schemas.interest import InterestMetaData
   
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