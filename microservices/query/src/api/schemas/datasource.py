from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel

class DataSourceType(str, Enum):
    API = "api"
    CSV = "csv"
    EXCEL = "excel"

class DataSourceConfig(BaseModel):
    url: Optional[str] = None
    method: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    headers: Optional[Dict[str, str]] = None
    renderData: Optional[str] = None
    file: Optional[str] = None

class DataSourceBase(BaseModel):
    type: DataSourceType
    config: DataSourceConfig
    fetch: str
class DataSourceCreate(DataSourceBase):
    id: str  # 手动输入的ID

class DataSourceUpdate(DataSourceBase):
    pass

class DataSource(DataSourceBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True