import torch,torch.nn.functional as F
import lightning as L
from ncps.torch import CfC
from ncps.wirings import AutoNCP

from api.dependencies.cfc import TaskStore

class CfcPredictor(L.LightningModule):
    def __init__(self, input_size, units, hidden_size=64):
        super().__init__()
        self.cfc = CfC(input_size, AutoNCP(units, hidden_size), batch_first=True)
        self.linear = torch.nn.Linear(hidden_size, 1)  # 预测单个值

    def forward(self, x):
        # x shape: (batch, seq_len, input_size)
        output, _ = self.cfc(x)
        # 取最后一个时间步的输出
        last_output = output[:, -1, :]
        return self.linear(last_output)

    def training_step(self, batch, batch_idx):
        x, y = batch
        y_hat = self(x)
        loss = F.mse_loss(y_hat, y)
        self.log("train_loss", loss)
        return loss

    def configure_optimizers(self):
        return torch.optim.Adam(self.parameters(), lr=1e-3)
    
class CfcFit(L.LightningModule):
    def __init__(self, input_size, units):
        super().__init__()
        self.cfc = CfC(input_size, AutoNCP(units, 1), batch_first=True,return_sequences=True)

    def forward(self, x):
        # x shape: (batch, seq_len, input_size)
        output, _ = self.cfc(x)
        return output

    def training_step(self, batch, batch_idx):
        x, y = batch
        y_hat = self(x)
        loss = F.mse_loss(y_hat, y)
        self.log("train_loss", loss)
        return loss

    def configure_optimizers(self):
        return torch.optim.Adam(self.parameters(), lr=1e-3)
    
class TrainingProgressCallback(L.Callback):
    """Lightning回调函数，用于捕捉训练进度"""
    
    def __init__(self, task_id: str, total_epochs: int,task_store:TaskStore):
        self.task_id = task_id
        self.total_epochs = total_epochs
        self.progress = 0.0
        self.task_store=task_store
    def on_train_epoch_end(self, trainer, pl_module):
        """每个epoch结束时触发更新"""
        current_epoch = trainer.current_epoch + 1  # epochs从0开始计数
        new_progress = min(100.0, (current_epoch / self.total_epochs) * 100)
        
        # 更新数据库中的任务状态
        self.task_store.update_task(
            task_id=self.task_id,
            progress=round(new_progress, 1),
        )
