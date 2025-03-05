from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from api.dependencies.database import get_db, transaction
from api.models.subject import SubjectData
from api.schemas.subject import SubjectDataCreate, SubjectDataResponse, SubjectDataUpdate
from api.models.interest import InterestCollection


router = APIRouter(prefix="/subjectData",tags=['subjectData'])

@router.post("/create",response_model=SubjectDataResponse)
@transaction
def create_subject_data(data:SubjectDataCreate,db: Session = Depends(get_db)):
    db_subject_data=SubjectData(data_type=data.data_type,subject_id=data.subject_id)
    db.add(db_subject_data)
    db.commit()
    db.refresh(db_subject_data)
    if len(data.collection_ids)>0:
        db.query(InterestCollection).filter(InterestCollection.id._in(data.collection_ids))\
            .update({InterestCollection.subject_data_id: db_subject_data.id})
        db.commit()
    return SubjectDataResponse.model_validate(db_subject_data)
@router.put("/{subject_data_id}/update",response_model=SubjectDataResponse)
def update_subject_data(subject_data_id:int,data:SubjectDataUpdate,db: Session = Depends(get_db)):
    db_subject_data=db.query(SubjectData).filter(SubjectData.id==subject_data_id)
    if db_subject_data is None:
        raise HTTPException(status_code=404, detail="SubjectData not found")
    for key, value in data.model_dump().items():
        setattr(db_subject_data, key, value)
    if len(data.add_collection_ids)>0:
        db.query(InterestCollection).filter(InterestCollection.id._in(data.collection_ids))\
            .update({InterestCollection.subject_data_id: db_subject_data.id})
    if len(data.delete_collection_ids)>0:
        db.query(InterestCollection).filter(InterestCollection.id._in(data.delete_collection_ids))\
            .update({InterestCollection.subject_data_id:None})
    db.commit()
    db.refresh(db_subject_data)
    return SubjectDataResponse.model_validate(db_subject_data)
@router.delete("/{subject_data_id}/delete",response_model=SubjectDataResponse)
@transaction
def delete_subject_data(subject_data_id:int,db: Session = Depends(get_db)):
    db_data=db.query(SubjectData).filter(SubjectData.id==subject_data_id)
    if db_data is None:
        raise HTTPException(status_code=404, detail="SubjectData not found")
    db.delete(db_data)
    db.commit()
    return SubjectDataResponse.model_validate(db_data)