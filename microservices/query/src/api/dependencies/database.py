import operator
from functools import wraps
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException
from config import get_settings
from sqlalchemy.ext.declarative import declarative_base

settings = get_settings()
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """获取主数据库连接，用于依赖注入"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_independent_db():
    """获取独立的数据库连接，用于后台任务等场景"""
    engine = create_engine(settings.database_url)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return Session()

def transaction(func):
    """事务处理装饰器，自动处理事务提交和回滚"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        db = kwargs.get('db')
        if not db:
            raise HTTPException(status_code=500, detail="Database session not found")
        
        try:
            if callable(func):
               result = await func(*args, **kwargs)
            else:
                raise HTTPException(status_code=500, detail="Provided function is not callable")
            return result
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=str(e))
    return wrapper

# 操作符映射
OPERATOR_MAP = {
    "eq": operator.eq,
    "ne": operator.ne,
    "gt": operator.gt,
    "ge": operator.ge,
    "lt": operator.lt,
    "le": operator.le,
    "in": lambda field, value: field.in_(value),
    "like": lambda field, value: field.like(f"%{value}%"),
}
