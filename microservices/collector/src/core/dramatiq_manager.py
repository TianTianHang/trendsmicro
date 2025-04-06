import dramatiq
from dramatiq.brokers.rabbitmq import RabbitmqBroker
from datetime import datetime, timedelta
from config import get_settings
from .jobs import execute_historical_task, execute_scheduled_task

settings = get_settings()
rabbitmq_broker = RabbitmqBroker(
    url=f"amqp://{settings.rabbitmq_username}:{settings.rabbitmq_username}@{settings.rabbitmq_host}:{settings.rabbitmq_port}"
)
dramatiq.set_broker(rabbitmq_broker)

class DramatiqManager:
    def __init__(self):
        self.broker = rabbitmq_broker
        
    def add_historical_job(self, task):
        """添加历史数据采集任务"""
        execute_historical_task.send(task)
        
    def add_cron_job(self, task):
        """添加定时任务"""
        interval_config = self._parse_interval(task.interval)
        delay = timedelta(**interval_config)
        execute_scheduled_task.send_with_options(
            args=(task,),
            delay=delay.total_seconds() * 1000  # 转换为毫秒
        )
        
    def _parse_interval(self, interval):
        """解析时间间隔(与原有逻辑保持一致)"""
        amount = int(interval[:-1])
        unit = interval[-1]
        if unit == 'h':
            return {'hours': amount}
        elif unit == 'd':
            return {'days': amount}
        elif unit == 'm':
            return {'minutes': amount}
        else:
            raise ValueError("Invalid interval format")

