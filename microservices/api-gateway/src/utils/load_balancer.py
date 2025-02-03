from typing import List, Dict

class RoundRobinBalancer:
    def __init__(self):
        self.index = 0

    def select_instance(self, instances: List[Dict]):
        if not instances:
            return None
        instance = instances[self.index % len(instances)]
        self.index += 1
        return instance