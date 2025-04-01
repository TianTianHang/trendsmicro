# src/api/dependencies/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import get_settings
from sqlalchemy.ext.declarative import declarative_base
settings = get_settings()
engine = create_engine(settings.database_url, pool_size=50,  # 持久连接的数量
    max_overflow=50,  # 允许超出pool_size的临时连接数
    pool_timeout=30  # 等待连接池返回连接的最长时间
    )
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()