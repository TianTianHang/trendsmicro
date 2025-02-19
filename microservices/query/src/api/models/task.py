from datetime import datetime
from sqlalchemy import Column, String, JSON, Float, DateTime
from api.dependencies.database import Base

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(String, primary_key=True, index=True)
    status = Column(String, nullable=False, default="processing")
    progress = Column(Float, default=0.0)
    result = Column(JSON)
    error = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
