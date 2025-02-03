#src/api/models/interest.py
from sqlalchemy import Boolean, Column, Integer, String, DateTime, UniqueConstraint
from api.dependencies.database import Base


class RegionInterest(Base):
    """地区兴趣数据模型"""
    __tablename__ = "region_interest"
    id = Column(Integer, primary_key=True)
    keyword = Column(String, nullable=False)       # 关键词
    geo_code = Column(String, nullable=False)      # 地区代码
    timeframe_start = Column(DateTime)             # 时间范围起点
    timeframe_end = Column(DateTime)               # 时间范围终点
    value = Column(Integer)                        # 兴趣值
    
    # 唯一约束：避免重复存储相同数据
    __table_args__ = (
        UniqueConstraint("keyword", "geo_code", "timeframe_start", "timeframe_end"),
    )

class TimeInterest(Base):
    """时间兴趣数据模型"""
    __tablename__ = "time_interest"
    id = Column(Integer, primary_key=True)
    keyword = Column(String, nullable=False)       # 关键词
    geo_code = Column(String)                      # 地区代码（可为空）
    time = Column(DateTime, nullable=False)        # 时间点
    value = Column(Integer)                        # 兴趣值
    is_partial = Column(Boolean)                   # 是否部分数据
    
    # 唯一约束
    __table_args__ = (
        UniqueConstraint("keyword", "time", "geo_code"),
    )