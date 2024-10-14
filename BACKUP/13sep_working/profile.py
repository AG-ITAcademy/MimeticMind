### profile.py - the main Profile and ProfileModel classes

import datetime
from sqlalchemy import create_engine, Column, Integer, String, Date, Float, Text
from sqlalchemy.orm import sessionmaker, declarative_base

# Define the base class for SQLAlchemy models
Base = declarative_base()

# SQLAlchemy Profile model
class ProfileModel(Base):
    __tablename__ = 'profiles'

    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_name = Column(String(255), nullable=True)
    created_at = Column(Date, default=datetime.datetime.utcnow)
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
    
class Profile:
    def __init__(self, db_session):
        self.session = db_session
        self.profile_name = None
        self.gender = None
        self.birth_date = None
        self.location = None
        self.education_level = None
        self.occupation = None
        self.income_range = None
        self.health_status = None
        self.ethnicity = None
        self.legal_status = None
        self.religion = None
        self.marital_status = None
        self.big_five_ocean_profile = None
        self.enneagram_profile = None
        self.mbti_profile = None
        self.personal_values = None
        self.hobbies = None
        self.llm_persona = None
        self.llm_typical_day = None

    def save_to_db(self):
        # Create an instance of the ProfileModel and save to the database
        profile_record = ProfileModel(
            profile_name=self.profile_name,
            gender=self.gender,
            birth_date=self.birth_date,
            location=self.location,
            education_level=self.education_level,
            occupation=self.occupation,
            income_range=self.income_range,
            health_status=self.health_status,
            ethnicity=self.ethnicity,
            legal_status=self.legal_status,
            religion=self.religion,
            marital_status=self.marital_status,
            big_five_ocean_profile=self.big_five_ocean_profile,
            enneagram_profile=self.enneagram_profile,
            mbti_profile=self.mbti_profile,
            personal_values=self.personal_values,
            hobbies=self.hobbies,
            llm_persona=self.llm_persona,
            llm_typical_day=self.llm_typical_day
        )
        self.session.add(profile_record)
        self.session.commit()
        return profile_record.id
