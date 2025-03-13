from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from api.dependencies.database import get_db, transaction
from api.models.subject import SubjectData
from api.schemas.subject import SubjectDataCreate, SubjectDataResponse, SubjectDataUpdate
from api.models.interest import InterestCollection, InterestMetaData


router = APIRouter(prefix="/subjectData",tags=['subjectData'])

@router.post("/create",response_model=SubjectDataResponse)
@transaction
async def create_subject_data(data:SubjectDataCreate,db: Session = Depends(get_db)):
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
@transaction
async def update_subject_data(subject_data_id:int,data:SubjectDataUpdate,db: Session = Depends(get_db)):
    db_subject_data = db.query(SubjectData).get(subject_data_id)
    if not db_subject_data:
        raise HTTPException(status_code=404, detail="SubjectData not found")
    
    # 更新可选的字段
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_subject_data, key, value)
    
    # 处理关联集合的更新
    def update_collections(collection_ids: List[int], subject_id: Optional[int]):
        if not collection_ids:
            return
        collections = db.query(InterestCollection).filter(InterestCollection.id.in_(collection_ids))
        for collection in collections:
            collection.subject_data_id = subject_id
            if collection.meta_data:
                collection.meta_data.subject_data_id = subject_id
    
    update_collections(data.add_collection_ids, subject_data_id)
    update_collections(data.delete_collection_ids, None)
    
    # 提交事务并刷新对象
    db.commit()
    db.refresh(db_subject_data)
    
    return SubjectDataResponse.model_validate(db_subject_data)
@router.delete("/{subject_data_id}/delete",response_model=SubjectDataResponse)
@transaction
async def delete_subject_data(subject_data_id:int,db: Session = Depends(get_db)):
    db_data=db.query(SubjectData).filter(SubjectData.id==subject_data_id)
    if db_data is None:
        raise HTTPException(status_code=404, detail="SubjectData not found")
    db.delete(db_data)
    db.commit()
    return SubjectDataResponse.model_validate(db_data)