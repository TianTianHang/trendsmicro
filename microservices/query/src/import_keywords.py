import csv
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from api.models.keywords import Word, Definition, Category  # 假设您的模型类存储在models.py文件中

# 创建引擎和会话
engine = create_engine('postgresql://admin:admin@localhost:5433/query')
Session = sessionmaker(bind=engine)
session = Session()

# 添加或获取类别
category_name = "Latin Phrases"
category_description = "Common Latin phrases and their meanings."
category = session.query(Category).filter_by(name=category_name).first()
if not category:
    category = Category(name=category_name, description=category_description)
    session.add(category)
    session.commit()

# 读取CSV文件并插入数据
with open('../default/latin_phrases_info.txt', 'r',encoding="utf-8") as file:
    reader = csv.DictReader(file)
    for row in reader:
        word = row['Phrase']
        pronunciation = row['Pronunciation']
        # 检查是否已存在
        if not session.query(Word).filter_by(word=word).first():
            new_word = Word(
                word=word,
                pronunciation=pronunciation,
                category_id=category.id
            )
            session.add(new_word)
            session.commit()  # 提交以获取ID
            definition = Definition(
                word_id=new_word.id,
                definition=word,  # 使用词/词组本身作为定义
                is_primary=True
            )
            session.add(definition)
            session.commit()

print("Data insertion completed.")