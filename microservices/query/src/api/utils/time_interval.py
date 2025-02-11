from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
def parse_interval(interval_str):
    """
    解析时间间隔字符串
    支持格式：YS（年）、MS（月）、H（小时）、M（分钟）、S（秒）
    """
    value = int(interval_str[:-2])  # 提取数字部分
    unit = interval_str[-2:]  # 提取单位部分

    if unit == "YS":
        return relativedelta(years=value)
    elif unit == "MS":
        return relativedelta(months=value)
    elif unit == "H":
        return timedelta(hours=value)
    elif unit == "M":
        return timedelta(minutes=value)
    elif unit == "S":
        return timedelta(seconds=value)
    else:
        raise ValueError("不支持的时间单位")