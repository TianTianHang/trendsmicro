from datetime import datetime
from enum import Enum
from typing import Dict, Any
from sqlalchemy import JSON, Column, DateTime, Enum as SQLEnum, String
from sqlalchemy.sql import func
from api.dependencies.database import Base

class DataSourceType(str, Enum):
    API = "api"
    CSV = "csv"
    EXCEL = "excel"

class DataSource(Base):
    __tablename__ = "datasources"

    id = Column(String(36), primary_key=True, index=True)
    type = Column(SQLEnum(DataSourceType), nullable=False)
    config = Column(JSON, nullable=False)
    fetch = Column(String(200), nullable=False)  
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type.value,
            "config": self.config,
            "fetch": self.fetch,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }