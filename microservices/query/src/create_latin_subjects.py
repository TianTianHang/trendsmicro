import csv
import requests
from typing import List
from time import sleep

# 配置信息
QUERY_API_URL = "http://localhost:8001/subject/create"
LATIN_FILE_PATH = "../default/latin_phrases_info.txt"


def read_latin_keywords() -> List[str]:
    """读取拉丁短语文件，返回关键词列表"""
    keywords = []
    with open(LATIN_FILE_PATH, mode='r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)  # 跳过标题行
        for row in reader:
            if row:  # 确保行不为空
                keywords.append(row[0])  # 第一列为关键词
    return keywords

def create_subject(keyword: str):
    """创建subject"""
    start_date = "2025-01-01"
    
    # 创建两种任务参数
    realtime_region = dict(
        data_type="region",
        keywords=[keyword],
        geo_code="",
        start_date=start_date,
        duration=365,
        interval="7d"
    )
    
    realtime_time = dict(
        data_type="time",
        keywords=[keyword],
        geo_code="",
        start_date=start_date,
        duration=365,
        interval="1d"
    )
    
  

    payload = {
        "name": keyword,
        "description": f"Latin phrase: {keyword}",
        "user_id": 1,  # 假设使用默认用户ID
        "parameters": [
            realtime_region,
            realtime_time,
        ]
    }
    
    response = requests.post(QUERY_API_URL, json=payload)
    if response.status_code != 200:
        print(f"Failed to create subject for {keyword}: {response.text}")
    else:
        print(f"Created subject for keyword: {keyword}")
    sleep(10)
def main():
    keywords = read_latin_keywords()
    for keyword in keywords:
        create_subject(keyword)

if __name__ == "__main__":
    main()