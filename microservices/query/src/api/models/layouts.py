import datetime
from sqlalchemy import JSON, Column, DateTime, String, BigInteger, func
from api.dependencies.database import Base

class SaveRecord(Base):
    __tablename__ = "save_records"
    
    id = Column(String, primary_key=True)  # 使用UUID作为主键
    name = Column(String, nullable=False)  # 保存名称
    version = Column(String, nullable=False)  # 版本号
    timestamp = Column(BigInteger, nullable=False)  # 时间戳，注意这里的数据类型已经改为BigInteger
    components = Column(JSON, nullable=False)  # 组件数据
    layouts = Column(JSON, nullable=False)  # 布局数据
    interlinks = Column(JSON, nullable=False)  # 关联数据
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())