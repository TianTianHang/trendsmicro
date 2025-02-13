from typing import Optional, List, Any
from pydantic import BaseModel

class Filter(BaseModel):
    field: str
    op: Optional[str] = "eq"  # 默认操作符为等于
    value: Any

class Sort(BaseModel):
    field: str
    order: Optional[str] = "asc"  # 默认升序

class QueryParams(BaseModel):
    filters: Optional[List[Filter]] = None
    sorts: Optional[List[Sort]] = None
    skip: Optional[int] = 0
    limit: Optional[int] = -1