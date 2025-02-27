import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from api.dependencies.database import get_db
from api.models.subject import Subject,SubjectData
from typing import List, Union
from api.schemas.subject import NotifyRequest, SubjectCreate, SubjectDataRegionResponse, SubjectDataResponse, SubjectDataTimeResponse, SubjectListResponse, SubjectResponse
from fastapi_events.dispatcher import dispatch


router = APIRouter(prefix="/subject")
#创建 subject
@router.post("/create", response_model=SubjectResponse)
def create_subject(subject: SubjectCreate, db: Session = Depends(get_db)):
    db_subject= Subject(description=subject.description,name=subject.name,user_id=subject.user_id, status="pending", parameters=[i.model_dump_json()for i in subject.parameters])
    db.add(db_subject)
    db.commit()
    db.refresh(db_subject)
    #触发事件 向collector发送通知，采集数据
    dispatch(event_name="subject_create", payload=db_subject)
    return {"subject_id": db_subject.subject_id}
#获取所有subject
@router.get("/list", response_model=List[SubjectListResponse])
def list_subjects(db: Session = Depends(get_db)):
    db_subjects = db.query(Subject).all()
    subjects_with_data_count = [
        SubjectListResponse(
            subject_id=subject.subject_id,
            name=subject.name,
            description=subject.description,
            status=subject.status,
            data_num=db.query(SubjectData).filter(SubjectData.subject_id == subject.subject_id).count()
        )
        for subject in db_subjects
    ]
    return subjects_with_data_count
# 获取subject对应的数据
@router.get("/{subject_id}/data", response_model=List[Union[SubjectDataTimeResponse,SubjectDataRegionResponse]])
def read_subject_data(subject_id: int, db: Session = Depends(get_db)):
    db_subject_data = db.query(SubjectData).filter(SubjectData.subject_id == subject_id).all()
    if not db_subject_data:
        raise HTTPException(status_code=404, detail="Subject data not found")
    return [
        SubjectDataTimeResponse(
            subject_id=data.subject_id,
            timestamp=data.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            data=json.loads(data.data),
            meta=json.loads(data.meta)
        ) if data.data_type == "time" else
        SubjectDataRegionResponse(
            subject_id=data.subject_id,
            timestamp=data.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            data=json.loads(data.data),
            meta=json.loads(data.meta)
        )
        for data in db_subject_data
    ]

#获取subject
@router.get("/{subject_id}", response_model=SubjectResponse)
def read_subjct(subject_id: int, db: Session = Depends(get_db)):
    db_subject = db.query(Subject).filter(Subject.subject_id==subject_id).first()
    if db_subject is None:
        raise HTTPException(status_code=404, detail="Subject not found")
    return db_subject



# 通知，collector 服务使用，采集完数据后将数据通知给subject服务（前端无用）
@router.post("/notification")
def notify(request: NotifyRequest):
    dispatch(event_name="subject_notify", payload=request)
    return {"status": "ok"}