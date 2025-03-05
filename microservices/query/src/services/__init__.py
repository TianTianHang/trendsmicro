from config import get_settings
from services.rabbitmq import RabbitMQClient
from services.registry import ConsulRegistry
from services.collector import CollectorService


setting= get_settings()
registry = ConsulRegistry(host=setting.consul_host, port=setting.consul_port)
collector = CollectorService(registry)