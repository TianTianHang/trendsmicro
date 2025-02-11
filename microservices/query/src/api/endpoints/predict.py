import os
from typing import List
import uuid
from fastapi import APIRouter, HTTPException
import torch
from core.models.cfc import CfcPredictor
from api.utils.create_dataset import create_sliding_window
from torch.utils.data import DataLoader,TensorDataset
import lightning as L
# 模型初始化
input_size = 1  # 输入特征维度
units = 64    # 模型单元数
hidden_size = 32  # 隐藏层大小
batch_size=32
epochs=15
router = APIRouter(prefix="/cfc")
@router.post("/train")
async def predict_time_interest_response(
    geo_code:str,
    data:List[float],
    window_size:int
):
        X,y=create_sliding_window(data,window_size)
        X = torch.tensor(X, dtype=torch.float32).unsqueeze(-1)  # 添加特征维度
        y = torch.tensor(y, dtype=torch.float32)
            
        dataset = TensorDataset(X, y)
        train_size = int(0.8 * len(dataset))
        val_size = len(dataset) - train_size
        train_dataset, val_dataset = torch.utils.data.random_split(dataset, [train_size, val_size])
            
        # 创建数据加载器
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=batch_size)
            
        # 初始化并训练模型
        model = CfcPredictor(input_size, units,hidden_size)
        trainer = L.Trainer(max_epochs=epochs)
        trainer.fit(model, train_loader, val_loader)
        # 生成模型ID
        model_id = f"{geo_code}_{uuid.uuid4().hex}"
    
        # 保存模型
        model_save_path = os.path.join("models", f"{model_id}.pt")
        torch.save(model.state_dict(), model_save_path)
    
        # 返回模型ID和训练状态
        return {
            "message": "Model trained successfully",
            "model_id": model_id,
            "model_save_path": model_save_path,
            "geo_code": geo_code,
            "status": "success"
        }
        
        
@router.post("/predict")
async def predict_time_interest_response(
    id:str,
    data:List[float],
    prediction_length: int = 1,  # 预测的长度
):
    try:
        # 读取模型
        model_path = os.path.join("models", f"{id}.pt")
        if not os.path.exists(model_path):
            raise HTTPException(status_code=404, detail=f"Model with id '{id}' not found")

        # 加载模型
        model= CfcPredictor(input_size, units,hidden_size)
        model.load_state_dict(torch.load(model_path))
        model.eval()  # 将模型设置为评估模式

        # 数据预处理
        x = torch.tensor(data, dtype=torch.float32).unsqueeze(-1).unsqueeze(0)  # 添加特征维度
        x = x.to(model.device)  # 将数据移动到模型所在的设备

       # 滚动预测
        predictions = []
        for _ in range(prediction_length):
            with torch.no_grad():
                y_pred = model(x).cpu()  # 预测下一个时间步的值
                predictions.append(float(y_pred.numpy().flatten()[0]))  # 将预测值添加到结果中
                x = torch.cat([x[:, 1:, :], y_pred.reshape(1, 1, 1)], dim=1)  # 更新输入数据，加入预测值

        # 返回预测结果
        return {"prediction": predictions}

    except torch.TorchError as e:
        raise HTTPException(status_code=500, detail=f"Model inference failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")