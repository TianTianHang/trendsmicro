from sqlalchemy.orm import Session
from api.models.torch_task import Task
import torch

class TaskStore:
    def __init__(self, db: Session):
        self.db = db

    def create_task(self, task_id: str) -> Task:
        task = Task(id=task_id,status="processing")
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def get_task(self, task_id: str) -> Task:
        return self.db.query(Task).filter(Task.id == task_id).first()

    def update_task(
        self,
        task_id: str,
        status: str = None,
        progress: float = None,
        result: dict = None,
        error: str = None
    ) -> Task:
        task = self.get_task(task_id)
        if task:
            if status is not None:
                task.status = status
            if progress is not None:
                task.progress = progress
            if result is not None:
                task.result = result
            if error is not None:
                task.error = error
            self.db.commit()
            self.db.refresh(task)
        return task
    def close(self):
        self.db.close()
        
        
MODEL_STORE: dict[str, torch.nn.Module] = {}  # 暂时保留内存存储，后续可改为数据库存储
