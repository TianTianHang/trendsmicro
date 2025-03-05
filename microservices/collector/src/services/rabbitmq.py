import aio_pika
from aio_pika import Message, ExchangeType, logger
from typing import Dict, List, Optional, Callable
import asyncio

from fastapi import FastAPI


from config import get_settings

settings = get_settings()
OnMessageCallback = Callable[[aio_pika.IncomingMessage], None]

class RabbitMQClient:
    _consumers: Dict[str, List[Callable]] = {}
    def __init__(self, queue):
        self.connection = None
        self.channel = None
        self.queue = queue

    async def connect(self):
        self.connection = await aio_pika.connect_robust(
            host=settings.rabbitmq_host,
            port=settings.rabbitmq_port,
            login=settings.rabbitmq_username,
            password=settings.rabbitmq_password
        )
        self.channel = await self.connection.channel()
        await self.channel.declare_queue(self.queue, durable=True)

    async def publish(self, message: str, properties: Optional[dict] = None):
        if not self.channel:
            await self.connect()
        await self.channel.default_exchange.publish(
            Message(body=message.encode(), **(properties or {})),
            routing_key=self.queue
        )

    async def consume(self, callback: OnMessageCallback):
        if not self.channel:
            await self.connect()
        queue = await self.channel.declare_queue(self.queue, durable=True)
        await queue.consume(callback)

    async def close(self):
        if self.connection:
            await self.connection.close()

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


    @classmethod
    def consumer(cls, queue: str):
        def decorator(func: Callable):
            if queue not in cls._consumers:
                cls._consumers[queue] = []
            cls._consumers[queue].append(func)
            return func
        return decorator
    @classmethod
    async def start_consumers(cls, app: FastAPI):
        # 在 FastAPI 启动时初始化所有消费者
        logger.info(cls._consumers.items())
        for queue, callbacks in cls._consumers.items():
           
            client = RabbitMQClient(queue)
            await client.connect()
            for callback in callbacks:
                await client.consume(callback)
            # 将连接保存在 app.state 中以便关闭
            if not hasattr(app.state, "rabbitmq_clients"):
                app.state.rabbitmq_clients = []
            app.state.rabbitmq_clients.append(client)

    @classmethod
    async def close_consumers(cls, app: FastAPI):
        # 在 FastAPI 关闭时关闭所有连接
        for client in getattr(app.state, "rabbitmq_clients", []):
            await client.close()