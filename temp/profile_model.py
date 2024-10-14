# profile_model.py

import datetime
from sqlalchemy import Column, Integer, String, DateTime, Float, Text, Date
from sqlalchemy.orm import declarative_base

# Define the base class for SQLAlchemy models
Base = declarative_base()

# SQLAlchemy Profile model
class ProfileModel(Base):
    __tablename__ = 'profiles'

    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_name = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    version = Column(Float, default=1.0)
    tags = Column(String, default='')
    
    # Demographic data
    birth_date = Column(Date, nullable=False)
    gender = Column(String(10), nullable=False)
    education_level = Column(String(255), nullable=False)
    occupation = Column(String(255), nullable=False)
    income_range = Column(String(50), nullable=True)
    location = Column(String(255), nullable=False)
    health_status = Column(String(255), nullable=False)
    ethnicity = Column(String(255), nullable=False)
    legal_status = Column(String(255), nullable=False)
    religion = Column(String(255), nullable=False)
    marital_status = Column(String(255), nullable=False)

    # Personality traits
    big_five_ocean_profile = Column(String(5), nullable=True)
    enneagram_profile = Column(Integer, nullable=True)
    mbti_profile = Column(String(4), nullable=True)
    personal_values = Column(String, nullable=True)
    hobbies = Column(String, nullable=True)

    llm_persona = Column(Text, nullable=True)
    llm_typical_day = Column(Text, nullable=True)
