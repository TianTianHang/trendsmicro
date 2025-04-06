from fastapi import APIRouter, Depends
import numpy as np
from api.schemas.moran import MoranInput, GlobalMoranOutput, LocalMoranOutput
from core.geo.moran import global_moran, local_moran

router = APIRouter(
    prefix="/moran",
    tags=["Moran's I"]
)

@router.post("/global", response_model=GlobalMoranOutput)
async def calculate_global_moran(input_data: MoranInput):
    y = np.array(input_data.data)
    iso_codes = input_data.iso_codes if hasattr(input_data, 'iso_codes') else None
    moran = global_moran(y, iso_codes)
    return {
        "I": moran.I,
        "p_value": moran.p_norm,
        "z_score": moran.z_norm
    }

@router.post("/local", response_model=LocalMoranOutput)
async def calculate_local_moran(input_data: MoranInput):
    y = np.array(input_data.data)
    iso_codes = input_data.iso_codes if hasattr(input_data, 'iso_codes') else None
    moran_local = local_moran(y, iso_codes)
    return {
        "I": [round(float(item), 5) if not np.isnan(item) else 0 for item in moran_local.Is],
        "p_values": [round(float(item), 5) if not np.isnan(item) else 0 for item in moran_local.p_sim],
        "z_scores": [round(float(item), 5) if not np.isnan(item) else 0 for item in moran_local.z_sim],
        "type": [int(item) if not np.isnan(item) else -999 for item in moran_local.q]  # 假设q是整数类型，用-999或其他标志表示缺失
    }
