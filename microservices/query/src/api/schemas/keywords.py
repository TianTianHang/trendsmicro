from datetime import datetime
from pydantic import BaseModel
from typing import Optional, List

class KeywordBase(BaseModel):
    word: str
    pronunciation: Optional[str] = None
    category_id: Optional[int] = None

class KeywordCreate(KeywordBase):
    pass

class KeywordUpdate(KeywordBase):
    pass

class Keyword(KeywordBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class DefinitionBase(BaseModel):
    word_id: int
    definition: str
    is_primary: Optional[bool] = False

class DefinitionCreate(DefinitionBase):
    pass

class DefinitionUpdate(DefinitionBase):
    pass

class Definition(DefinitionBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    parent_id: Optional[int] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(CategoryBase):
    pass

class Category(CategoryBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]
    children: List['Category'] = []

    class Config:
        from_attributes = True


class KeywordWithDetails(Keyword):
    definitions: List[Definition] = []
    category: Optional[Category] = None

    class Config:
        from_attributes = True
