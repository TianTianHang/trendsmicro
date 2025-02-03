from fastapi import FastAPI
from microservices.query.src.api.config import get_settings
from microservices.query.src.api.endpoints import interest

app = FastAPI()

app.include_router(interest.router)
setting= get_settings()
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=setting.port)
