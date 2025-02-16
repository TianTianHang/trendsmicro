from typing import Optional, List, Any, Union
from pydantic import BaseModel

class FitData(BaseModel):
    timespans: List[int]
    values: List[Union[int,float]]
