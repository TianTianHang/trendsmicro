from sqlalchemy import JSON, Column, DateTime, Integer, String, func
from api.dependencies.database import Base
class Task(Base):
    __tablename__ = 'torch_tasks'
    id = Column(Integer, primary_key=True, index=True)
    status = Column(String, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    progress =Column(Integer)
    result = Column(JSON) # Union[RealtimeTask,HistoricalTask] 的数组
    error = Column(String)