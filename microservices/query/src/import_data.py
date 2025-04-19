from datetime import datetime
import json
import os
import pandas as pd
from pandas.errors import EmptyDataError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from api.models.subject import Subject, SubjectData
from api.dependencies.database import Base
from api.models.interest import InterestCollection, InterestMetaData, RegionInterest, TimeInterest

DATABASE_URL = "postgresql://admin:admin@localhost:5433/query"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def import_data(data_type,data_path,geo_code=""):
    db = SessionLocal()
    try:
       for root, dirs, files in os.walk(data_path):
            for file in files:
                if file.endswith('.csv'):
                    # 构造文件路径
                    file_path = os.path.join(root, file)
                
                    # 提取文件名中的keyword、start_date、end_date
                    file_name = os.path.splitext(file)[0]  # 去掉文件扩展名
                    parts = file_name.split('-')
                    if len(parts) >= 3:
                        keywords:str = parts[0]  # 关键词部分
                        start_date = '-'.join(parts[1:4]) # 开始日期
                        end_date ='-'.join(parts[4:7]) # 结束日期
                        timeframe = f'{start_date} {end_date}'  # 时间范围
                    
                        # 读取CSV文件到DataFrame
                        try:
                            df = pd.read_csv(file_path)
                        except EmptyDataError:
                            print(f"空文件跳过: {file_path}")
                            continue
                    
                        df.dropna(inplace=True)
                        ic=InterestCollection(interest_type = data_type)
                        meta=InterestMetaData(keywords = keywords.split(","),
                                                geo_code = geo_code,
                                                timeframe_start = datetime.strptime(start_date,"%Y-%m-%d").date(),
                                                timeframe_end= datetime.strptime(end_date,"%Y-%m-%d").date())
                       
                        db.add(meta)
                        db.commit()
                        db.refresh(meta)
                        ic.meta_data_id=meta.id
                        db.add(ic)
                        db.commit()
                        db.refresh(ic)
                        interests=[]
                        for index, row in df.iterrows():
                            row_dict = row.to_dict()
                            if data_type == 'time':
                                values = {k: v for k, v in row_dict.items() if k not in ['time [UTC]', 'isPartial']}
                                interests.append(TimeInterest(time_utc=row['time [UTC]'], values=values,
                                                              is_partial=row.get('isPartial',False), collect_id=ic.id))
                            elif data_type == 'region':
                                values = {k: v for k, v in row_dict.items() if k not in ['geoName', 'geoCode']}
                                interests.append(RegionInterest(geo_name=row['geoName'], values=values,
                                                                geo_code=row['geoCode'], collect_id=ic.id))
                        db.add_all(interests)
                        db.commit()
    except Exception as e:
        db.rollback()
        print(f"数据导入失败: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
    import_data("region","C:\\Users\\Administrator\\Desktop\\new,novel")
