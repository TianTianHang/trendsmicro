#src/api/models/tasks.py
from sqlalchemy import Column, Integer, String, JSON, Boolean, DateTime
from datetime import datetime
from api.dependencies.database import Base

class HistoricalTask(Base):
    __tablename__ = "historical_tasks"
    id = Column(Integer, primary_key=True)
    job_type = Column(String(10)) # time or region
    keyword = Column(String(255), nullable=False)
    geo_code = Column(String(10))
    start_date = Column(String(10))  # 格式："YYYY-MM-DD"
    end_date = Column(String(10))
    interval = Column(String(2))     # "YS"（年）或 "MS"（月）
    status = Column(String(20), default="pending")  # pending/running/completed/failed
    created_at = Column(DateTime, default=datetime.utcnow)

class ScheduledTask(Base):
    __tablename__ = "scheduled_tasks"
    id = Column(Integer, primary_key=True)
    job_type = Column(String(10)) # time or region
    cron_expression = Column(String(50), nullable=False)  # 如 "0 3 * * *"
    keyword = Column(String(255), nullable=False)
    geo_code = Column(String(10))
    interval = Column(String(2), default="MS")
    enabled = Column(Boolean, default=True)