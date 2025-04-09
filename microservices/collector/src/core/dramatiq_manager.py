from datetime import datetime, timedelta
from .jobs import execute_historical_task, execute_scheduled_task



class DramatiqManager:
  
        
    def add_historical_job(self, task):
        """添加历史数据采集任务"""
        execute_historical_task.send(**task.to_dict())
        
    def add_cron_job(self, task):
        """添加定时任务"""
        interval_config = self._parse_interval(task.interval)
        execute_scheduled_task.send_with_options(
            kwargs={
                **task.to_dict(),
                'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            },
            delay=timedelta(**interval_config).total_seconds() * 1000  # 转换为毫秒
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

