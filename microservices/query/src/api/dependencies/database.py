# src/api/dependencies/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import get_settings
from sqlalchemy.ext.declarative import declarative_base
from gateway import CollectorGateway
import asyncio
import logging

settings = get_settings()
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def sync_data():
    """通过网关从collector同步数据"""
    from api.models.interest import RegionInterest, TimeInterest
    
    gateway = CollectorGateway()
    data = await gateway.sync_data()
    
    with get_db() as db:
        # 同步RegionInterest
        for region in data["regions"]:
            if not db.query(RegionInterest).filter_by(
                keyword=region["keyword"],
                geo_code=region["geo_code"],
                timeframe_start=region["timeframe_start"],
                timeframe_end=region["timeframe_end"]
            ).first():
                db.add(RegionInterest(
                    keyword=region["keyword"],
                    geo_code=region["geo_code"],
                    timeframe_start=region["timeframe_start"],
                    timeframe_end=region["timeframe_end"],
                    value=region["value"]
                ))
        
        # 同步TimeInterest
        for time in data["times"]:
            if not db.query(TimeInterest).filter_by(
                keyword=time["keyword"],
                time=time["time"],
                geo_code=time["geo_code"]
            ).first():
                db.add(TimeInterest(
                    keyword=time["keyword"],
                    geo_code=time["geo_code"],
                    time=time["time"],
                    value=time["value"],
                    is_partial=time["is_partial"]
                ))
        
        db.commit()

# 设置SQLAlchemy日志
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
