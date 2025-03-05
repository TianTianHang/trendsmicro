import json
from sqlalchemy import Boolean, Column, Date, Integer, String, JSON, ForeignKey
from sqlalchemy.orm import relationship

from api.dependencies.database import Base

class InterestCollection(Base):
    __tablename__ = 'interest_collection'
    id = Column(Integer, primary_key=True, index=True)
    interest_type = Column(String)
    subject_data_id = Column(Integer, ForeignKey('subject_data.id'))
    subject_data = relationship("SubjectData", back_populates="interest_collections")
    meta_data_id = Column(Integer, ForeignKey('interest_meta_data.id'))
    meta_data = relationship("InterestMetaData", back_populates="interest_collection")
    time_interests = relationship("TimeInterest", back_populates="interest_collection")
    region_interests = relationship("RegionInterest", back_populates="interest_collection")
        
class TimeInterest(Base):
    __tablename__ = 'time_interests'
    id = Column(Integer, primary_key=True, index=True)
    time_utc = Column(String, index=True)
    is_partial = Column(Boolean, default=False)
    values = Column(JSON)
    collect_id = Column(Integer, ForeignKey('interest_collection.id'))
    interest_collection = relationship("InterestCollection", back_populates="time_interests")
    def convert(self):
        from api.schemas.interest import TimeInterest as TimeSchema
        return TimeSchema(time_utc=self.time_utc,is_partial=self.is_partial,**self.values)
class RegionInterest(Base):
    __tablename__ = 'region_interests'
    id = Column(Integer, primary_key=True, index=True)
    geo_name = Column(String, index=True)
    geo_code = Column(String, index=True)
    values = Column(JSON) #[k:v]
    collect_id = Column(Integer, ForeignKey('interest_collection.id'))
    interest_collection = relationship("InterestCollection", back_populates="region_interests")
    def convert(self):
        from api.schemas.interest import RegionInterest as RegionSchema
        return RegionSchema(geo_name=self.geo_name,geo_code=self.geo_code,**self.values)
class InterestMetaData(Base):
    __tablename__ = 'interest_meta_data'
    id = Column(Integer, primary_key=True, index=True)
    keywords = Column(JSON)
    geo_code = Column(String, index=True)
    timeframe_start = Column(Date)
    timeframe_end = Column(Date)
    subject_data_id = Column(Integer, ForeignKey('subject_data.id'))
    subject_data = relationship("SubjectData", back_populates="meta_data")
    interest_collection = relationship("InterestCollection", back_populates="meta_data", uselist=False)
    def convert(self):
        from api.schemas.interest import InterestMetaData as MetaSchema
        return MetaSchema(keywords=self.keywords,geo_code=self.geo_code,
                          timeframe_start=self.timeframe_start,timeframe_end=self.timeframe_end)