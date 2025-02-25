from config import get_settings
from services.registry import ConsulRegistry
from services.query import QueryService


setting= get_settings()
registry = ConsulRegistry(host=setting.consul_host, port=setting.consul_port)
query = QueryService(registry)