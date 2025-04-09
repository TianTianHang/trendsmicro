#src/api/endpoints/tasks.py
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Body, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from core import scheduler_manager,aio_scheduler
from api.dependencies.database import get_db
from fastapi_events.dispatcher import dispatch
from api.models.tasks import HistoricalTask, ScheduledTask
from api.schemas.tasks import (
    HistoricalTaskRequest,
    ScheduledTaskRequest,
    HistoricalTaskResponse,
    ScheduledTaskResponse
)


router = APIRouter(prefix="/tasks")



@router.post("/historical")
async def create_historical_task(
    request: HistoricalTaskRequest, 
    db: Session = Depends(get_db)
):
    """提交历史数据采集任务"""
    # 保存任务到数据库
    task = HistoricalTask(**request.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    dispatch(event_name="historical_task_create",payload=task)
    return {"task_id": task.id}

@router.post("/scheduled")
async def create_scheduled_task(
    request: ScheduledTaskRequest,
    db: Session = Depends(get_db)
):
    """创建定时采集任务"""
    
    # 保存任务到数据库
    task = ScheduledTask(**request.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    # 添加到调度器
    aio_scheduler.add_cron_job(task)
    
    return {"task_id": task.id}

@router.get("/historical", response_model=List[HistoricalTaskResponse])
def list_historical_tasks(db: Session = Depends(get_db)):
    """查询所有历史任务"""
    return db.query(HistoricalTask).all()

@router.get("/scheduled", response_model=List[ScheduledTaskResponse])
def list_scheduled_tasks(db: Session = Depends(get_db)):
    """查询所有定时任务"""
    return db.query(ScheduledTask).all()


@router.post("/historical/{task_id}/terminate",deprecated=True)
def terminate_historical_task(
    task_id: int, 
    db: Session = Depends(get_db)
):
    task = db.query(HistoricalTask).get(task_id)
    if not task:
        raise HTTPException(404, "任务不存在")
    
    # 如果任务正在运行
    if task.status == "running":
        scheduler_manager.remove_job(f"historical_{task_id}")
        task.status = "failed"
        db.commit()
    
    return {"message": "任务已终止"}

@router.post("/historical/{task_id}/retry")
async def retry_historical_task(
    task_id: int, 
    db: Session = Depends(get_db)
):
    task = db.query(HistoricalTask).get(task_id)
    if not task:
        raise HTTPException(400, "任务不存在")
    
    # 如果任务失败
    if task.status == "failed":
       dispatch(event_name="historical_task_create",payload=task)
    else:
        raise HTTPException(403, "操作不合法")
    return {"message": "任务已重新开始"}

@router.post("/scheduled/{task_id}/toggle")
def toggle_scheduled_task(
    task_id: int = Path(...),
    enabled: bool=Body(...),
    db: Session = Depends(get_db)
):
    task = db.query(ScheduledTask).get(task_id)
    if not task:
        raise HTTPException(404, "任务不存在")
    
    # 调度器操作
    job_id = f"scheduled_{task_id}"
    if enabled:
        aio_scheduler.scheduler.resume_job(job_id)
    else:
        aio_scheduler.scheduler.pause_job(job_id)
    
    # 更新数据库状态
    task.enabled = enabled
    db.commit()
    return {"message": "状态已更新"}
