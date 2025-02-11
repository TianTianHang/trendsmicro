# src/core/utils/time_splitter.py
import pandas as pd

def split_time_ranges(start_date: str, end_date: str, interval: str) -> list:
    """
    根据时间间隔分割时间段
    Args:
        interval: 
            "YS" - 按年分割 (2004-01-01 到 2005-01-01)
            "MS" - 按月分割 (2004-01-01 到 2004-02-01)
    """
    if interval == None:
        return [(start_date,end_date)]
    try:
        dates = pd.date_range(start=start_date, end=end_date, freq=interval)
        ranges = []
        for i in range(len(dates)-1):
            ranges.append((
                dates[i].strftime("%Y-%m-%d"), 
                dates[i+1].strftime("%Y-%m-%d")
            ))
        # 处理最后一个时间段
        if ranges and ranges[-1][1] < end_date:
            ranges.append((ranges[-1][1], end_date))
        return ranges
    except ValueError as e:
        raise ValueError(f"无效的时间间隔参数: {interval}") from e