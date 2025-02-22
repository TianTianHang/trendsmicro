from config import get_settings
from utils.load_balancer import RoundRobinBalancer
from services.registry import ConsulRegistry

setting = get_settings()
# 初始化核心组件
registry = ConsulRegistry(host=setting.consul_host, port=setting.consul_port)
balancer = RoundRobinBalancer()
