from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from api.dependencies.database import get_db
from api.models.subject import Subject,SubjectData
from typing import List
from api.schemas.subject import NotifyRequest, SubjectCreate, SubjectDataResponse, SubjectResponse
from fastapi_events.dispatcher import dispatch


router = APIRouter(prefix="/subject")

@router.post("/create", response_model=SubjectResponse)
def create_subject(subject: SubjectCreate, db: Session = Depends(get_db)):
    db_subject= Subject(user_id=subject.user_id, status="pending", parameters=[i.model_dump_json()for i in subject.parameters])
    db.add(db_subject)
    db.commit()
    db.refresh(db_subject)
    dispatch(event_name="subject_create", payload=db_subject)
    return {"subject_id": db_subject.subject_id}

@router.get("/{subject_id}", response_model=SubjectResponse)
def read_task(subject_id: int, db: Session = Depends(get_db)):
    db_subject = db.query(Subject).filter(Subject.subject_id==subject_id).first()
    if db_subject is None:
        raise HTTPException(status_code=404, detail="Subject not found")
    return db_subject

@router.get("/{subject_id}/data", response_model=List[SubjectDataResponse])
def read_task_data(subject_id: int, db: Session = Depends(get_db)):
    db_subject_data = db.query(SubjectData).filter(SubjectData.subject_id == subject_id).all()
    if not db_subject_data:
        raise HTTPException(status_code=404, detail="Subject data not found")
    return db_subject_data

@router.post("/notification")
def notify(request: NotifyRequest):
    dispatch(event_name="subject_notify", payload=request)
    return {"status": "ok"}