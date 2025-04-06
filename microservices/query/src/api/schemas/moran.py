from pydantic import BaseModel
from typing import List, Literal
from enum import Enum

class MissingDataMethod(str, Enum):
    DROP = 'drop'
    INTERPOLATE = 'interpolate'

class MoranInput(BaseModel):
    data: List[float]
    iso_codes: List[str]
    missing_data_method: MissingDataMethod = MissingDataMethod.DROP

class GlobalMoranOutput(BaseModel):
    I: float
    p_value: float
    z_score: float

class LocalMoranOutput(BaseModel):
    I: List[float]
    p_values: List[float]
    z_scores: List[float]
    type: List[int]
