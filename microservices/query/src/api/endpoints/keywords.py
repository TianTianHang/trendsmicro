from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from api.dependencies.database import get_db, transaction
from api.models.keywords import Word, Definition, Category
from api.schemas.keywords import KeywordCreate, KeywordUpdate, Keyword as KeywordSchema, KeywordWithDetails, DefinitionCreate, DefinitionUpdate,Definition as DefinitionSchema, CategoryCreate, CategoryUpdate, Category as  CategorySchema

router = APIRouter(prefix='/keywords',tags=['keywords'])

@router.post("/words/create", response_model=KeywordSchema)
@transaction
async def create_keyword(keyword: KeywordCreate, db: Session = Depends(get_db)):
    db_keyword = Word(**keyword.model_dump())
    db.add(db_keyword)
    db.commit()
    db.refresh(db_keyword)
    return KeywordSchema.model_validate(db_keyword)

@router.get("/words/{keyword_id}", response_model=KeywordWithDetails)
@transaction
async def read_keyword(keyword_id: int, db: Session = Depends(get_db)):
    db_keyword = db.query(Word).filter(Word.id == keyword_id).first()
    if db_keyword is None:
        raise HTTPException(status_code=404, detail="Keyword not found")
    
    # 获取关联的定义
    definitions = db.query(Definition).filter(Definition.word_id == keyword_id).all()
    
    # 获取关联的类别
    category = None
    if db_keyword.category_id:
        category = db.query(Category).filter(Category.id == db_keyword.category_id).first()
    
    keyword_data = KeywordSchema.model_validate(db_keyword)
    return KeywordWithDetails(
        **keyword_data.model_dump(),
        definitions=definitions,
        category=category
    )

@router.put("/words/{keyword_id}/update", response_model=KeywordSchema)
@transaction
async def update_keyword(keyword_id: int, keyword: KeywordUpdate, db: Session = Depends(get_db)):
    db_keyword = db.query(Word).filter(Word.id == keyword_id).first()
    if db_keyword is None:
        raise HTTPException(status_code=404, detail="Keyword not found")
    for key, value in keyword.model_dump().items():
        setattr(db_keyword, key, value)
    db.commit()
    db.refresh(db_keyword)
    return KeywordSchema.model_validate(db_keyword)

@router.delete("/words/{keyword_id}/delete", response_model=KeywordSchema)
@transaction
async def delete_keyword(keyword_id: int, db: Session = Depends(get_db)):
    db_keyword = db.query(Word).filter(Word.id == keyword_id).first()
    if db_keyword is None:
        raise HTTPException(status_code=404, detail="Keyword not found")
    db.delete(db_keyword)
    db.commit()
    return KeywordSchema.model_validate(db_keyword)



@router.post("/definitions/create", response_model=DefinitionSchema)
@transaction
async def create_definition(definition: DefinitionCreate, db: Session = Depends(get_db)):
    db_definition = Definition(**definition.model_dump())
    db.add(db_definition)
    db.commit()
    db.refresh(db_definition)
    return DefinitionSchema.model_validate(db_definition)

@router.get("/definitions/{definition_id}", response_model=DefinitionSchema)
@transaction
def read_definition(definition_id: int, db: Session = Depends(get_db)):
    db_definition = db.query(Definition).filter(Definition.id == definition_id).first()
    if db_definition is None:
        raise HTTPException(status_code=404, detail="Definition not found")
    return DefinitionSchema.model_validate(db_definition)

@router.put("/definitions/{definition_id}/update", response_model=DefinitionSchema)
@transaction
def update_definition(definition_id: int, definition: DefinitionUpdate, db: Session = Depends(get_db)):
    db_definition = db.query(Definition).filter(Definition.id == definition_id).first()
    if db_definition is None:
        raise HTTPException(status_code=404, detail="Definition not found")
    for key, value in definition.model_dump().items():
        setattr(db_definition, key, value)
    db.commit()
    db.refresh(db_definition)
    return DefinitionSchema.model_validate(db_definition)

@router.delete("/definitions/{definition_id}/delete", response_model=DefinitionSchema)
@transaction
async def delete_definition(definition_id: int, db: Session = Depends(get_db)):
    db_definition = db.query(Definition).filter(Definition.id == definition_id).first()
    if db_definition is None:
        raise HTTPException(status_code=404, detail="Definition not found")
    db.delete(db_definition)
    db.commit()
    return DefinitionSchema.model_validate(db_definition)

@router.post("/categories/create", response_model=CategorySchema)
@transaction
async def create_category(category: CategoryCreate, db: Session = Depends(get_db)):
    # 检查父类别是否存在
    if category.parent_id:
        parent_category = db.query(Category).filter(Category.id == category.parent_id).first()
        if not parent_category:
            raise HTTPException(status_code=404, detail="Parent category not found")
    
    db_category = Category(**category.model_dump())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return CategorySchema.model_validate(db_category)

@router.get("/words/list", response_model=list[KeywordWithDetails])
@transaction
async def list_words(db: Session = Depends(get_db)):
    db_words = db.query(Word).all()
    result = []
    for word in db_words:
        # 获取关联的定义
        definitions = db.query(Definition).filter(Definition.word_id == word.id).all()
        
        # 获取关联的类别
        category = None
        if word.category_id:
            category = db.query(Category).filter(Category.id == word.category_id).first()
        
        keyword_data = KeywordSchema.model_validate(word)
        result.append(KeywordWithDetails(
            **keyword_data.model_dump(),
            definitions=definitions,
            category=category
        ))
    return result

def build_category_tree(categories, parent_id=None):
    tree = []
    for category in categories:
        if category.parent_id == parent_id:
            children = build_category_tree(categories, category.id)
            if children:
                category.children = children
            tree.append(category)
    return tree

@router.get("/categories/list", response_model=list[CategorySchema])
@transaction
async def list_categories(db: Session = Depends(get_db)):
    db_categories = db.query(Category).all()
    category_tree = build_category_tree(db_categories)
    return [CategorySchema.model_validate(category) for category in category_tree]

@router.get("/categories/{category_id}", response_model=CategorySchema)
@transaction
async def read_category(category_id: int, db: Session = Depends(get_db)):
    db_category = db.query(Category).filter(Category.id == category_id).first()
    if db_category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # 获取子类别
    children = db.query(Category).filter(Category.parent_id == category_id).all()
    if children:
        db_category.children = children
    
    return CategorySchema.model_validate(db_category)

@router.put("/categories/{category_id}/update", response_model=CategorySchema)
@transaction
async def update_category(category_id: int, category: CategoryUpdate, db: Session = Depends(get_db)):
    db_category = db.query(Category).filter(Category.id == category_id).first()
    if db_category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    for key, value in category.model_dump().items():
        setattr(db_category, key, value)
    db.commit()
    db.refresh(db_category)
    return CategorySchema.model_validate(db_category)

@router.delete("/categories/{category_id}/delete", response_model=CategorySchema)
@transaction
async def delete_category(category_id: int, db: Session = Depends(get_db)):
    db_category = db.query(Category).filter(Category.id == category_id).first()
    if db_category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    db.delete(db_category)
    db.commit()
    return CategorySchema.model_validate(db_category)
