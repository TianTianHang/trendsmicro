import asyncio
from functools import lru_cache
import os
from typing import List
import uuid
from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends
import torch
from core.fit.cfc import CfcFit, CfcPredictor, TrainingProgressCallback
from api.utils.create_dataset import create_sliding_window
from torch.utils.data import DataLoader,TensorDataset
import lightning as L
from sqlalchemy.orm import Session

from api.schemas.cfc import  FitRequest, FitResponse
from api.utils.cfc import get_data_hash
from api.dependencies.cfc import MODEL_STORE, TaskStore
from api.dependencies.database import get_db, get_independent_db

@lru_cache
def get_predict_parm():
    # 模型初始化
    input_size = 1  # 输入特征维度
    units = 64    # 模型单元数
    hidden_size = 32  # 隐藏层大小
    batch_size=32
    epochs=15
    return input_size,units,hidden_size,batch_size,epochs

router = APIRouter(prefix="/cfc")

@router.post("/train")
async def predict_time_interest_response(
    geo_code:str,
    data:List[float],
    window_size:int
):  
    input_size,units,hidden_size,batch_size,epochs=get_predict_parm()
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
    input_size,units,hidden_size,batch_size,epochs=get_predict_parm()
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


###################fit######################
async def async_train_task(data: FitRequest):
    """真实训练任务"""
    db = get_independent_db()
    data_hash = get_data_hash(data.model_dump())
    task_store = TaskStore(db)
    
    try:
       
        
        # 将CPU密集型操作放到线程池中执行
        def train_model():
            # 数据预处理
            X = torch.tensor(data.timespans, dtype=torch.float32).reshape(1, -1, 1)
            y = torch.tensor(data.values, dtype=torch.float32).reshape(1, -1, 1) / 100
            total_epochs = 50
            progress_callback = TrainingProgressCallback(
                task_id=data_hash, 
                total_epochs=total_epochs,
                task_store=task_store
            )
            
            # 模型训练
            model = CfcFit(input_size=1, units=128)
            trainer = L.Trainer(
                max_epochs=total_epochs,
                callbacks=[progress_callback],
                enable_progress_bar=False
            )
            trainer.fit(model, (X, y))
            
            # 存储模型
            MODEL_STORE[data_hash] = model
            
            # 生成预测结果
            with torch.no_grad():
                prediction = model(X)
            return (prediction.reshape(-1) * 100).tolist()
        
        # 异步执行训练任务
        fit_values = await asyncio.to_thread(train_model)
        
        # 更新任务状态
        task_store.update_task(
            task_id=data_hash,
            status="completed",
            result={
                "timespans": data.timespans,
                "values": [round(v, 2) for v in fit_values]
            }
        )
    except Exception as e:
        task_store.update_task(
            task_id=data_hash,
            status="failed",
            error=str(e)
        )
    finally:
        # 防止进度显示超过100%
        task = task_store.get_task(data_hash)
        if task.status == "processing":
            task_store.update_task(
                task_id=data_hash,
                progress=100.0,
                status="completed"
            )
        task_store.close()

@router.post("/fit", response_model=FitResponse)
async def predict_time_interest_response(
    request: FitRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    data_hash = get_data_hash(request.model_dump())
    task_store = TaskStore(db)
    
    # 检查任务是否存在
    task = task_store.get_task(data_hash)
    if not task:
        # 新任务：创建并添加后台任务
        task_store.create_task(data_hash)
        background_tasks.add_task(async_train_task, request)
        return FitResponse(
            task_id=data_hash,
            status="processing"
        )
    
    # 返回现有任务状态
    return FitResponse(
        task_id=data_hash,
        status=task.status,
        result=task.result
    )
    
@router.get("/fit/{task_id}", response_model=FitResponse)
async def get_task_status(
    task_id: str,
    db: Session = Depends(get_db)
):
    task_store = TaskStore(db)
    task = task_store.get_task(task_id)
    if not task:
        return FitResponse(
            task_id=task_id,
            status="not_found"
        )
    
    return FitResponse(
        task_id=task_id,
        status=task.status,
        result=task.result,
        progress=task.progress
    )
