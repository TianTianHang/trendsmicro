from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.dependencies.database import get_db
from api.models.interest import InterestCollection
from api.schemas.interest import InterestCollectionRequest, InterestCollectionResponse, InterestMetaData
from fastapi import Query

router = APIRouter(
    prefix="/interests",
    tags=["interests"]
)

@router.get("/collections/notBind", response_model=List[InterestCollectionResponse])
def get_interest_collections(
    interest_type:str=Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1),
    db: Session = Depends(get_db)
):
    filters = InterestCollection.subject_data_id.is_(None)
    if interest_type:
        filters = filters & (InterestCollection.interest_type == interest_type)
    result = db.query(InterestCollection).filter(filters).offset(skip).limit(limit)
    return [InterestCollectionResponse(
                    id=r.id,
                    interest_type=r.interest_type,
                    subject_data_id=r.subject_data_id,
                    meta_data=r.meta_data.convert()
        ) for r in result.all()]

@router.get("/collections/bind", response_model=List[InterestCollectionResponse])
def get_interest_collections(
    interest_type:str=Query(None),
    subject_data_ids: str = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1),
    db: Session = Depends(get_db)
):
    subject_data_ids = subject_data_ids.split(",") if subject_data_ids else []
    filters = InterestCollection.subject_data_id.in_(subject_data_ids)
    if interest_type:
        filters = filters & (InterestCollection.interest_type == interest_type)
    result = db.query(InterestCollection).filter(filters).offset(skip).limit(limit)
    return [InterestCollectionResponse(
                    id=r.id,
                    interest_type=r.interest_type,
                    subject_data_id=r.subject_data_id,
                    meta_data=r.meta_data.convert()
        ) for r in result.all()]