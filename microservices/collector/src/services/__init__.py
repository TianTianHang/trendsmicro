from config import get_settings
from services.rabbitmq import RabbitMQClient
from services.registry import ConsulRegistry


setting= get_settings()
registry = ConsulRegistry(host=setting.consul_host, port=setting.consul_port)