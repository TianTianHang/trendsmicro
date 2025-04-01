import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from sqlalchemy.orm import Session
from api.dependencies.database import get_db
from api.models.layouts import SaveRecord

router = APIRouter(prefix='/layouts', tags=['layouts'])

class SaveRequest(BaseModel):
    id:str
    name: str
    version: str
    timestamp: int
    components: dict
    layouts: dict
    interlinks: dict

class LayoutResponse(BaseModel):
    id: str
    name: str
    version: str
    timestamp: int
    components: dict
    layouts: dict
    interlinks: dict
    created_at: datetime
    updated_at: datetime

@router.post("/save", response_model=LayoutResponse)
async def save_data(data: SaveRequest, db: Session = Depends(get_db)):
    db_record=db.query(SaveRecord).filter(SaveRecord.id==data.id).first()
    if db_record:
        db_record.name=data.name
        db_record.version=data.version
        db_record.timestamp=data.timestamp
        db_record.components=data.components
        db_record.layouts=data.layouts
        db_record.interlinks=data.interlinks
        db.commit()
        db.refresh(db_record)
        return db_record
    else:
        record = SaveRecord(
            id=data.id,
            name=data.name,
            version=data.version,
            timestamp=data.timestamp,
            components=data.components,
            layouts=data.layouts,
            interlinks=data.interlinks
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

@router.get("/list", response_model=List[LayoutResponse])
async def get_all_data(db: Session = Depends(get_db)):
    records = db.query(SaveRecord).all()
    return records

@router.delete("/delete")
async def delete_data(record_id: str, db: Session = Depends(get_db)):
    record = db.query(SaveRecord).filter(SaveRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    db.delete(record)
    db.commit()
    return {"message": "Record deleted successfully"}