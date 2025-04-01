import datetime
from sqlalchemy import JSON, Column, DateTime, Integer, String
from api.dependencies.database import Base
class SaveRecord(Base):
    __tablename__ = "save_records"
    
    id = Column(String, primary_key=True)  # 使用UUID作为主键
    name = Column(String, nullable=False)  # 保存名称
    version = Column(String, nullable=False)  # 版本号
    timestamp = Column(Integer, nullable=False)  # 时间戳
    components = Column(JSON, nullable=False)  # 组件数据
    layouts = Column(JSON, nullable=False)  # 布局数据
    interlinks = Column(JSON, nullable=False)  # 关联数据
    created_at = Column(DateTime, default=datetime.utcnow)  # 创建时间
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # 更新时间