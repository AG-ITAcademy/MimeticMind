from sqlalchemy import Column, Integer, String, Date, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class CompletedSurvey(Base):
    __tablename__ = 'vw_completed_surveys'
    
    project_survey_id = Column(Integer, primary_key=True)
    survey_alias = Column(String)
    survey_template_id = Column(Integer)
    project_id = Column(Integer)
    segment_id = Column(Integer)
    created_at = Column(DateTime)
    credits = Column(Integer)

class CompletedSurveyQuestion(Base):
    __tablename__ = 'vw_completed_survey_questions'
    
    question_template_id = Column(Integer, primary_key=True)
    answer_schema = Column(String)
    project_survey_id = Column(Integer)
    user_id = Column(Integer)

class ScaleResponse(Base):
    __tablename__ = 'vw_scale_responses'
    
    project_survey_id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    interaction_id = Column(Integer, primary_key=True)
    profile_id = Column(Integer)
    gender = Column(String)
    birth_date = Column(Date)
    location = Column(String)
    occupation = Column(String)
    income_range = Column(String)
    education_level = Column(String)
    religion = Column(String)
    ethnicity = Column(String)
    hobbies = Column(String)
    health_status = Column(String)
    marital_status = Column(String)
    query_template_id = Column(Integer)
    question_text = Column(Text)
    rating = Column(Integer)

class OpenEndedResponse(Base):
    __tablename__ = 'vw_open_ended_responses'
    
    project_survey_id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    interaction_id = Column(Integer, primary_key=True)
    profile_id = Column(Integer)
    gender = Column(String)
    birth_date = Column(Date)
    location = Column(String)
    occupation = Column(String)
    income_range = Column(String)
    education_level = Column(String)
    religion = Column(String)
    ethnicity = Column(String)
    hobbies = Column(String)
    health_status = Column(String)
    marital_status = Column(String)
    query_template_id = Column(Integer)
    question_text = Column(Text)
    response = Column(Text)

class MultipleChoiceResponse(Base):
    __tablename__ = 'vw_multiple_choice_responses'
    
    project_survey_id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    interaction_id = Column(Integer, primary_key=True)
    profile_id = Column(Integer)
    gender = Column(String)
    birth_date = Column(Date)
    location = Column(String)
    occupation = Column(String)
    income_range = Column(String)
    education_level = Column(String)
    religion = Column(String)
    ethnicity = Column(String)
    hobbies = Column(String)
    health_status = Column(String)
    marital_status = Column(String)
    query_template_id = Column(Integer)
    question_text = Column(Text)
    choice = Column(String)

class YesNoResponse(Base):
    __tablename__ = 'vw_yes_no_responses'
    
    project_survey_id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    interaction_id = Column(Integer, primary_key=True)
    profile_id = Column(Integer)
    gender = Column(String)
    birth_date = Column(Date)
    location = Column(String)
    occupation = Column(String)
    income_range = Column(String)
    education_level = Column(String)
    religion = Column(String)
    ethnicity = Column(String)
    hobbies = Column(String)
    health_status = Column(String)
    marital_status = Column(String)
    query_template_id = Column(Integer)
    question_text = Column(Text)
    answer = Column(String)

class RankingResponse(Base):
    __tablename__ = 'vw_ranking_responses'
    
    project_survey_id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    interaction_id = Column(Integer, primary_key=True)
    profile_id = Column(Integer)
    gender = Column(String)
    birth_date = Column(Date)
    location = Column(String)
    occupation = Column(String)
    income_range = Column(String)
    education_level = Column(String)
    religion = Column(String)
    ethnicity = Column(String)
    hobbies = Column(String)
    health_status = Column(String)
    marital_status = Column(String)
    query_template_id = Column(Integer)
    question_text = Column(Text)
    item = Column(String)
    rank = Column(Integer)