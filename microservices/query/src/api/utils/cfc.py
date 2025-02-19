import hashlib
import json


def get_data_hash(data: dict) -> str:
    """生成稳定数据哈希"""
    sorted_data = json.dumps(data, sort_keys=True)
    return hashlib.sha256(sorted_data.encode()).hexdigest()
   