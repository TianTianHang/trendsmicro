from functools import lru_cache
import geopandas as gpd
from libpysal import weights
from esda.moran import Moran, Moran_Local
import numpy as np
import os
from scipy.interpolate import griddata
from typing import Literal
shp_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data','ne_110m_admin_0_countries.shp')
if not os.path.exists(shp_path):
    raise FileNotFoundError(f"Shapefile not found at {shp_path}")
    
gdf = gpd.read_file(shp_path)


@lru_cache(maxsize=128)
def _match_data_with_countries(y_tuple, iso_codes, target_iso_codes):
    """匹配输入数据与国家代码(带缓存)"""
    y = np.array(y_tuple)
    idx = [i for i, code in enumerate(iso_codes) if code in target_iso_codes]
    matched_y = y[[i for i, code in enumerate(target_iso_codes) if code in iso_codes]]
    return idx, matched_y

def _handle_missing_data(y, iso_codes, method: Literal['drop', 'interpolate'] = 'drop'):
    """处理缺失数据"""
    if method == 'drop':
        valid_idx = ~np.isnan(y)
        return y[valid_idx], [iso_codes[i] for i in range(len(iso_codes)) if valid_idx[i]]
    elif method == 'interpolate':
        # 使用空间插值填充缺失值
        valid_idx = ~np.isnan(y)
        if np.sum(valid_idx) < 3:
            raise ValueError("Not enough valid points for interpolation")
        
        # 获取有效点的坐标
        
        coords = np.array([(geom.centroid.x, geom.centroid.y) for geom in gdf.geometry])
        
        # 插值
        y_interp = griddata(coords[valid_idx], y[valid_idx], coords, method='nearest')
        return y_interp, iso_codes
    else:
        raise ValueError(f"Unknown method: {method}")
@lru_cache(maxsize=128)
def global_moran(y, iso_codes, missing_data_method: Literal['drop', 'interpolate'] = 'drop'):
    """
    计算全局莫兰指数
    :param y: numpy array, 待分析的空间数据
    :param iso_codes: list, 输入数据对应的国家代码（ISO_A2）
    :param missing_data_method: str, 缺失数据处理方法 ('drop' 或 'interpolate')
    :return: Moran对象，包含莫兰指数、p值等统计量
    """
    country_iso = gdf['ISO_A2'].values
    # 处理缺失数据
    y_processed, iso_processed = _handle_missing_data(y, iso_codes, missing_data_method)
    # 匹配数据与国家代码(转换为元组用于缓存)
    idx, matched_y = _match_data_with_countries(tuple(y_processed), country_iso, tuple(iso_processed))
    # 获取对应的权重矩阵(带缓存)
    w = _get_weights(gdf.iloc[idx])
    moran = Moran(matched_y, w)
    return moran
@lru_cache(maxsize=128)
def local_moran(y, iso_codes, missing_data_method: Literal['drop', 'interpolate'] = 'drop'):
    """
    计算局部莫兰指数
    :param y: numpy array, 待分析的空间数据
    :param iso_codes: list, 输入数据对应的国家代码（ISO_A2）
    :param missing_data_method: str, 缺失数据处理方法 ('drop' 或 'interpolate')
    :return: Moran_Local对象，包含局部莫兰指数、p值等统计量
    """
    country_iso = gdf['ISO_A2'].values
    # 处理缺失数据
    y_processed, iso_processed = _handle_missing_data(y, iso_codes, missing_data_method)
    # 匹配数据与国家代码(转换为元组用于缓存)
    idx, matched_y = _match_data_with_countries(tuple(y_processed), country_iso, tuple(iso_processed))
    # 获取对应的权重矩阵(带缓存)
    w = _get_weights(gdf.iloc[idx])
    moran_local = Moran_Local(matched_y, w)
    return moran_local
@lru_cache(maxsize=128)
def _get_weights(gdf_subset):
    """获取权重矩阵(带缓存)"""
    return weights.Queen.from_dataframe(gdf_subset)

