from typing import List, Dict, Optional

class RoundRobinBalancer:
    def __init__(self):
        self.index = 0

    def select_instance(self, instances: List[Dict], service_id: Optional[str] = None):
        """
        选择服务实例。
        如果指定了 service_id，则优先选择匹配的服务实例。
        如果未指定 service_id，则使用轮询算法选择实例。
        """
        if not instances:
            return None

        if service_id:
            # 如果指定了服务号，优先选择匹配的服务实例
            for instance in instances:
                if instance.instance_id  == service_id:
                    return instance
            return None  # 如果未找到匹配的服务号，返回 None

        # 如果未指定服务号，使用轮询算法选择实例
        instance = instances[self.index % len(instances)]
        self.index += 1
        return instance