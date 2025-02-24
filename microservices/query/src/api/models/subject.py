from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

from api.dependencies.database import Base



class Subject(Base):
    __tablename__ = 'subjects'
    subject_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    status = Column(String, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    parameters = Column(JSON) # Union[RealtimeTask,HistoricalTask] 的数组
    collector_task_id = Column(Integer)
    
class SubjectData(Base):
    __tablename__ = 'subject_data'
    id = Column(Integer, primary_key=True, index=True)
    subject_id = Column(Integer, ForeignKey('subjects.subject_id'), index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    data = Column(JSON)
    meta = Column(JSON)
