import numpy as np
import pandas as pd
from trendspy.utils import extract_column

class TrendsDataConverter:
    """趋势数据转换器，用于处理Google Trends API返回的原始数据"""
    
    @staticmethod
    def token_to_bullets(token_data):
        items = token_data.get('request', {}).get('comparisonItem', [])
        bullets = [item.get('complexKeywordsRestriction', {}).get('keyword', [''])[0].get('value','') for item in items]
        metadata = [next(iter(item.get('geo', {'':'unk'}).values()), 'unk') for item in items]
        if len(set(metadata))>1:
            bullets = [b+' | '+m for b,m in zip(bullets, metadata)]
        metadata = [item.get('time', '').replace('\\', '') for item in items]
        if len(set(metadata))>1:
            bullets = [b+' | '+m for b,m in zip(bullets, metadata)]
            
        return bullets
        
    @staticmethod
    def interest_over_time(widget_data, keywords, time_as_index=True):
        """
        将随时间变化的兴趣数据转换为pandas DataFrame
        Converts interest over time data to a pandas DataFrame.

        Parameters:
            widget_data (dict): 原始API响应数据 | Raw API response data
            keywords (list): 关键词列表，用于列名 | List of keywords for column names
            time_as_index (bool): 是否使用时间作为DataFrame索引 | Use time as DataFrame index

        Returns:
            pandas.DataFrame: 处理后的随时间变化兴趣数据 | Processed interest over time data
        """
        # 获取时间线数据，处理默认值和timelineData键
        timeline_data = widget_data
        timeline_data = timeline_data.get('default', timeline_data)
        timeline_data = timeline_data.get('timelineData', timeline_data)
        if not timeline_data:
            return pd.DataFrame(columns=keywords)
        def convert_elements(lst):
            return [int(item) if item != "<1" else 0.1 for item in lst]
        # 提取值数据并转换为DataFrame格式
        df_data = np.array(extract_column(timeline_data, 'formattedValue',f=lambda x:convert_elements(x))).reshape(len(timeline_data), -1)
        df_data = dict(zip(keywords, df_data.T))
        
        # 检查并添加部分数据标记
        if ('isPartial' in timeline_data[-1]) or any('isPartial' in row for row in timeline_data):
            df_data['isPartial'] = extract_column(timeline_data, 'isPartial', False)

        # 处理时间戳数据
        timestamps = extract_column(timeline_data, 'time', f=lambda x:int(x) if x else None)
        timestamps = np.array(timestamps, dtype='datetime64[s]').astype('datetime64[ns]')
        # timestamps += np.timedelta64(get_utc_offset_minutes(), 'm')  # 如果需要UTC偏移可以取消注释
        
        # 根据参数返回不同格式的DataFrame
        if time_as_index:
            return pd.DataFrame(df_data, index=pd.DatetimeIndex(timestamps, name='time [UTC]'))
        return pd.DataFrame({'time':timestamps, **df_data})
    
    @staticmethod
    def geo_data(widget_data, bullets=None):
        """
        处理地理数据，转换为包含地理信息的DataFrame
        Process geo data and convert to DataFrame with geographic information

        Parameters:
            widget_data (dict): 原始API响应数据 | Raw API response data
            bullets (list): 关键词别名列表，用于列名 | List of keyword aliases for column names

        Returns:
            pandas.DataFrame: 处理后的地理数据 | Processed geo data
        """
        # 获取地理数据
        data = widget_data.get('default', {}).get('geoMapData', [])
        # 过滤掉没有数据的条目
        filtered_data = list(filter(lambda item:item['hasData'][0], data))
        if not filtered_data:
            return pd.DataFrame()
        
        # 确定关键词数量并设置默认列名
        num_keywords = len(filtered_data[0]['value'])
        if not bullets:
            bullets = ['keyword_'+str(i) for i in range(num_keywords)]

        # 提取可用的地理信息列
        found_cols = set(filtered_data[0].keys()) & {'coordinates', 'geoCode', 'geoName', 'value'}
        df_data = {}
        df_data['geoName'] = extract_column(filtered_data, 'geoName')  # 地理名称
        
        # 添加地理编码(如果有)
        if 'geoCode' in found_cols:
            df_data['geoCode'] = extract_column(filtered_data, 'geoCode')
        
        # 添加经纬度坐标(如果有)
        if 'coordinates' in found_cols:
            df_data['lat'] = extract_column(filtered_data, 'coordinates', f=lambda x:x['lat'])
            df_data['lng'] = extract_column(filtered_data, 'coordinates', f=lambda x:x['lng'])

        # 处理值数据并添加到DataFrame
        values = np.array(extract_column(filter_data, 'formattedValue',f=lambda x:int(x) if x!="<1" else 0.1)).reshape(len(filtered_data), -1)
        for keyword,values_row in zip(bullets, values.T):
            df_data[keyword] = values_row
            
        return pd.DataFrame(df_data)