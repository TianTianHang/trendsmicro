from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, func
from api.dependencies.database import Base
from sqlalchemy.orm import relationship
class Word(Base):
    __tablename__ = 'words'

    id = Column(Integer, primary_key=True)
    word = Column(String(255), nullable=False, unique=True)
    pronunciation = Column(String(255))
    category_id = Column(Integer, ForeignKey('categories.id'))
    created_at = Column(DateTime,server_default=func.now())
    updated_at = Column(DateTime,onupdate=func.now())

    category = relationship("Category", back_populates="words")
    definitions = relationship("Definition", back_populates="word")
    
class Definition(Base):
    __tablename__ = 'definitions'

    id = Column(Integer, primary_key=True)
    word_id = Column(Integer, ForeignKey('words.id'), nullable=False)
    definition = Column(Text, nullable=False)
    is_primary = Column(Boolean, default=False)
    created_at = Column(DateTime,server_default=func.now())
    updated_at = Column(DateTime,onupdate=func.now())


    word = relationship("Word", back_populates="definitions")

class Category(Base):
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text)
    parent_id = Column(Integer, ForeignKey('categories.id'), nullable=True)
    created_at = Column(DateTime,server_default=func.now())
    updated_at = Column(DateTime,onupdate=func.now())

    words = relationship("Word", back_populates="category")
    parent = relationship("Category", remote_side=[id], back_populates="children")
    children = relationship("Category", back_populates="parent")
