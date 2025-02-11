from typing import Optional, List, Any
from pydantic import BaseModel

class Filter(BaseModel):
    field: str
    op: Optional[str] = "eq"  # 默认操作符为等于
    value: Any