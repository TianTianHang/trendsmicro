#src/api/models/tasks.py
from sqlalchemy import  Column, Date, ForeignKey, Index, Integer, String, JSON, Boolean, DateTime, UniqueConstraint
from datetime import date, datetime
from api.dependencies.database import Base

class HistoricalTask(Base):
    __tablename__ = "historical_tasks"
    id = Column(Integer, primary_key=True)
    job_type = Column(String(10)) # time or region
    keywords = Column(JSON, nullable=False)
    geo_code = Column(String(10))
    start_date = Column(String(10))  # 格式："YYYY-MM-DD"
    end_date = Column(String(10))
    interval = Column(String(2))     # "YS"（年）或 "MS"（月）
    status = Column(String(20), default="pending")  # pending/running/completed/failed
    created_at = Column(DateTime, default=datetime.utcnow)
    schedule_id = Column(Integer,ForeignKey('scheduled_tasks.id'))
    
class ScheduledTask(Base):
    __tablename__ = "scheduled_tasks"
    id = Column(Integer, primary_key=True)
    job_type = Column(String(10)) # time or region
    keywords = Column(JSON, nullable=False)
    geo_code = Column(String(10))
    duration = Column(Integer)
    start_date = Column(DateTime, nullable=False)  
    interval = Column(String(2), default="MS") #任务执行的间隔时间
    enabled = Column(Boolean, default=True)
   
    
    # 请求历史记录模型
class RequestHistory(Base):
    """记录已处理的Trends API请求参数，避免重复查询"""
    __tablename__ = "request_history"
    id = Column(Integer, primary_key=True)
    job_type = Column(String(10)) # time or region
    keywords = Column(JSON, nullable=False)       # 关键词
    geo_code = Column(String, nullable=False)      # 地区代码
    timeframe_start = Column(Date, nullable=False) # 时间范围起点
    timeframe_end = Column(Date, nullable=False)   # 时间范围终点
    created_at = Column(Date, default=date.today())# 记录创建时间
    status = Column(String(20), default="created") #created/success/failed 
    # 唯一约束：确保同一请求参数不会重复记录
    __table_args__ = (
        UniqueConstraint("keywords","job_type", "geo_code", "timeframe_start", "timeframe_end"),
        Index('idx_request_params', 'job_type','keywords', 'geo_code', 'timeframe_start')
    )