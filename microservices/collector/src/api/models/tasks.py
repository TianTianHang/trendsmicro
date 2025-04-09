#src/api/models/tasks.py
from sqlalchemy import  Column, Date, ForeignKey, Index, Integer, String, JSON, Boolean, DateTime, UniqueConstraint
from datetime import date, datetime
from api.dependencies.database import Base
from sqlalchemy.dialects.postgresql import JSONB
class HistoricalTask(Base):
    __tablename__ = "historical_tasks"
    id = Column(Integer, primary_key=True)
    job_type = Column(String(10)) # time or region
    keywords = Column(JSONB, nullable=False)
    geo_code = Column(String(10))
    start_date = Column(Date)  # 格式："YYYY-MM-DD"
    end_date = Column(Date)
    interval = Column(String(10))     # "YS"（年）或 "MS"（月）
    status = Column(String(20), default="pending")  # pending/running/completed/failed
    created_at = Column(DateTime, default=datetime.now())
    schedule_id = Column(Integer,ForeignKey('scheduled_tasks.id'))
    def to_dict(self):
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, (date, datetime)):
                # 将日期或日期时间转换为ISO格式字符串
                result[column.name] = value.isoformat()
            else:
                result[column.name] = value
        return result
class ScheduledTask(Base):
    __tablename__ = "scheduled_tasks"
    id = Column(Integer, primary_key=True)
    job_type = Column(String(10)) # time or region
    keywords = Column(JSONB, nullable=False)
    geo_code = Column(String(10))
    duration = Column(Integer)
    start_date = Column(Date, nullable=False)  
    interval = Column(String(10), default="1d") #任务执行的间隔时间
    enabled = Column(Boolean, default=True)
    def to_dict(self):
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, (date, datetime)):
                # 将日期或日期时间转换为ISO格式字符串
                result[column.name] = value.isoformat()
            else:
                result[column.name] = value
        return result
    
    # 请求历史记录模型
class RequestHistory(Base):
    """记录已处理的Trends API请求参数，避免重复查询"""
    __tablename__ = "request_history"
    id = Column(Integer, primary_key=True)
    job_type = Column(String(10)) # time or region
    keywords = Column(JSONB, nullable=False)       # 关键词
    geo_code = Column(String, nullable=False)      # 地区代码
    timeframe_start = Column(Date, nullable=False) # 时间范围起点
    timeframe_end = Column(Date, nullable=False)   # 时间范围终点
    created_at = Column(DateTime, default=datetime.now())# 记录创建时间
    status = Column(String(20), default="created") #created/success/failed
    interest_id = Column(Integer) 
    # 唯一约束：确保同一请求参数不会重复记录
    __table_args__ = (
        UniqueConstraint("job_type", "geo_code", "timeframe_start", "timeframe_end"),
        Index('idx_request_params', 'job_type', 'geo_code', 'timeframe_start')
    )
    