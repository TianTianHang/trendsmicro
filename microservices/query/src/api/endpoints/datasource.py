from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from api.schemas.datasource import (
    DataSource,
    DataSourceCreate,
    DataSourceUpdate
)
from api.models.datasource import DataSource as DataSourceModel
from api.dependencies.database import get_db

router = APIRouter(prefix="/datasources")

@router.post("/create", response_model=DataSource)
async def create_datasource(
    datasource: DataSourceCreate,
    db: Session = Depends(get_db)
):
    # 检查ID是否已存在
    if db.query(DataSourceModel).filter(DataSourceModel.id == datasource.id).first():
        raise HTTPException(status_code=400, detail="DataSource ID already exists")
        
    db_datasource = DataSourceModel(
        id=datasource.id,
        type=datasource.type,
        config=datasource.config.model_dump(),
        fetch=datasource.fetch
    )
    db.add(db_datasource)
    db.commit()
    db.refresh(db_datasource)
    return db_datasource.to_dict()

@router.get("/list", response_model=List[DataSource])
async def list_datasources(db: Session = Depends(get_db)):
    datasources = db.query(DataSourceModel).all()
    return [ds.to_dict() for ds in datasources]

@router.get("/{id}", response_model=DataSource)
async def get_datasource(id: str, db: Session = Depends(get_db)):
    datasource = db.query(DataSourceModel).filter(DataSourceModel.id == id).first()
    if not datasource:
        raise HTTPException(status_code=404, detail="DataSource not found")
    return datasource.to_dict()

@router.put("/{id}/update", response_model=DataSource)
async def update_datasource(
    id: str,
    datasource: DataSourceUpdate, 
    db: Session = Depends(get_db)
):
    db_datasource = db.query(DataSourceModel).filter(DataSourceModel.id == id).first()
    if not db_datasource:
        raise HTTPException(status_code=404, detail="DataSource not found")
    
    db_datasource.type = datasource.type
    db_datasource.config = datasource.config.model_dump()
    db_datasource.fetch = datasource.fetch
    db.commit()
    db.refresh(db_datasource)
    return db_datasource.to_dict()

@router.delete("/{id}/delete")
async def delete_datasource(id: str, db: Session = Depends(get_db)):
    datasource = db.query(DataSourceModel).filter(DataSourceModel.id == id).first()
    if not datasource:
        raise HTTPException(status_code=404, detail="DataSource not found")
    
    db.delete(datasource)
    db.commit()
    return {"message": "DataSource deleted"}