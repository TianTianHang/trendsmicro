from utils.load_balancer import RoundRobinBalancer
from services.registry import ServiceRegistry
# 初始化核心组件
registry = ServiceRegistry()
balancer = RoundRobinBalancer()
