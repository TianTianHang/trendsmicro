import json
import os
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from api.models.subject import Subject, SubjectData
from api.dependencies.database import Base

DATABASE_URL = "sqlite:///query.db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def import_data(parameters,data):
    db = SessionLocal()
    try:
        # 示例数据
        subject = Subject(name="latin",user_id=1, status="completed", parameters=json.dumps(parameters))
        db.add(subject)
        db.commit()
        db.refresh(subject)
        for i in range(len(parameters)):
            all_data = {"data":[],"meta":[]}
            for root, dirs, files in os.walk(data[i]):
                for file in files:
                    if file.endswith('.csv'):
                        # 构造文件路径
                        file_path = os.path.join(root, file)
                
                        # 提取文件名中的keyword、start_date、end_date
                        file_name = os.path.splitext(file)[0]  # 去掉文件扩展名
                        parts = file_name.split('-')
                        if len(parts) >= 3:
                            keyword = parts[0]  # 关键词部分
                            start_date = '-'.join(parts[1:4]) # 开始日期
                            end_date ='-'.join(parts[4:7]) # 结束日期
                            timeframe = f'{start_date} {end_date}'  # 时间范围
                    
                            # 读取CSV文件到DataFrame
                            df = pd.read_csv(file_path)
                            df.dropna(inplace=True)
                            all_data['data'].append(df.to_dict(orient="records"))
                            
                            all_data['meta'].append({
                                "keywords": [keyword],
                                "timeframe_start": start_date,
                                "timeframe_end": end_date,
                                "geo_code":""
                            })
            subject_data = SubjectData(data_type=parameters[i]['data_type'],subject_id=subject.subject_id, data=json.dumps(all_data['data']),meta=json.dumps(all_data['meta']))
            db.add(subject_data)
            db.commit()
        
        print(f"数据导入成功: Subject ID = {subject.subject_id}")
    except Exception as e:
        db.rollback()
        print(f"数据导入失败: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
    parameters=[
        {
            "type": "historical",
            "data_type": "region",
            "keywords": ["latin(language)"],
            "geo_code": "",
            "start_date": "2004-01-01",
            "end_date": "2024-01-01",
            "interval": "yearly"
        },{
            "type": "historical",
            "data_type": "time",
            "keywords": ["latin(language)"],
            "geo_code": "",
            "start_date": "2004-01-01",
            "end_date": "2024-01-01"
        }
    ]
    data=["C:\\Users\\a2450\\Desktop\\project\\find-latin-word\\data\\yearly\\original_data\\latin(language)","C:\\Users\\a2450\\Desktop\\project\\find-latin-word\\data\\over_time\\original_data\\latin(language)"]
    import_data(parameters,data)
