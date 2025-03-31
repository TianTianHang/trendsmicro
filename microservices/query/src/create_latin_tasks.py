import csv
from datetime import datetime
from time import sleep
import requests
from typing import List

# 配置信息
COLLECTOR_API_URL = "http://localhost:8002/tasks/scheduled"
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

def create_scheduled_task(keyword: str, job_type: str):
    """创建定时任务"""
    payload = {
        "keywords": [keyword],
        "job_type": job_type,
        "interval": "1d",  # 每天执行
        "start_date": "2025-01-01",
        "duration":365
    }
    if job_type=="region":
        payload["interval"]="7d"
    response = requests.post(COLLECTOR_API_URL, json=payload)
    if response.status_code != 200:
        print(f"Failed to create task for {keyword} ({job_type}): {response.text}")

def main():
    keywords = read_latin_keywords()
    for keyword in keywords:
        # 为每个关键词创建两个任务
        create_scheduled_task(keyword, "region")
        create_scheduled_task(keyword, "time")
        print(f"Created tasks for keyword: {keyword}")
        sleep(10)   

if __name__ == "__main__":
    main()