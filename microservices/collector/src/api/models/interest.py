#src/api/models/interest.py
from sqlalchemy import JSON, Boolean, Column, Date, Index, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from api.dependencies.database import Base


class RegionInterest(Base):
    """地区兴趣数据模型"""
    __tablename__ = "region_interest"
    id = Column(Integer, primary_key=True)
    keywords = Column(JSONB, nullable=False)      # 关键词
    geo_code = Column(String, nullable=False)      # 地区代码
    timeframe_start = Column(Date)             # 时间范围起点
    timeframe_end = Column(Date)               # 时间范围终点
    data = Column(JSON)                        # 数据
    task_id = Column(String)                   # 关联任务ID
  
    class Config:
        orm_mode = True
    # 唯一约束：避免重复存储相同数据
    __table_args__ = (
        UniqueConstraint("geo_code", "timeframe_start", "timeframe_end","keywords"),
        Index('idx_region', 'geo_code'),
        Index('idx_timeframe', 'timeframe_start')
    )


class TimeInterest(Base):
    """时间兴趣数据模型"""
    __tablename__ = "time_interest"
    id = Column(Integer, primary_key=True)
    keywords = Column(JSONB, nullable=False)       # 关键词
    geo_code = Column(String)                      # 地区代码（可为空）
    timeframe_start = Column(Date)             # 时间范围起点
    timeframe_end = Column(Date)               # 时间范围终点
    data = Column(JSON)                        # 数据
    task_id = Column(String)                   # 关联任务ID 
   
    
    class Config:
        orm_mode = True
    # 唯一约束
    __table_args__ = (
        UniqueConstraint("timeframe_start", "geo_code","timeframe_end","keywords"),
        Index('idx_time', 'timeframe_start'),
        Index('idx_geo_time', 'geo_code', 'timeframe_start')
    )
