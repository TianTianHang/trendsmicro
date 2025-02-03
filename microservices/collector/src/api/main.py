#src/api/main.py
from fastapi import FastAPI
from api.dependencies.database import engine,Base
from api.dependencies.scheduler import scheduler_manager
from api.endpoints import tasks
# 初始化调度器
Base.metadata.create_all(bind=engine)
async def lifespan_handler(app: FastAPI):
    scheduler_manager.scheduler.start()
    # 新增状态同步
    scheduler_manager.sync_job_status()
    
    yield
    scheduler_manager.scheduler.shutdown()



app = FastAPI(title="Trends Collector API",lifespan=lifespan_handler)
app.include_router(tasks.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)