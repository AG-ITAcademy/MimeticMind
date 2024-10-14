# data_access/data_access_layer.py

import os
import json
import logging
from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey, Text, DateTime
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from config import Config

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the base class for declarative models
Base = declarative_base()

# Define SQLAlchemy Models Corresponding to Your Database Tables

class AnalysisMethod(Base):
    __tablename__ = 'analysis_methods'
    
    id = Column(Integer, primary_key=True)
    analysis_method = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    sample_use_case = Column(Text, nullable=False)
    module_name = Column(String, nullable=False) 
    class_name = Column(String, nullable=False)
 
    answer_schemas = relationship("AnalysisMethodAnswerSchema", back_populates="analysis_method")


class AnalysisMethodAnswerSchema(Base):
    __tablename__ = 'analysis_method_answer_schema'
    
    id = Column(Integer, primary_key=True)
    answer_schema = Column(String, nullable=False)
    analysis_method_id = Column(Integer, ForeignKey('analysis_methods.id'), nullable=False)
    enabled = Column(Boolean, nullable=False)
    
    analysis_method = relationship("AnalysisMethod", back_populates="answer_schemas")


class QueryTemplate(Base):
    __tablename__ = 'query_templates'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    query_text = Column(Text, nullable=False)
    schema = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
    customizable_parameters = Column(Text)
    focus_factor_id = Column(Integer)
    description = Column(Text)
    
    interactions = relationship("Interaction", back_populates="query_template")


class Profile(Base):
    __tablename__ = 'profiles'
    
    id = Column(Integer, primary_key=True)
    profile_name = Column(String, nullable=False)
    created_at = Column(DateTime)
    version = Column(Integer)
    tags = Column(String)
    birth_date = Column(String)
    gender = Column(String)
    education_level = Column(String)
    occupation = Column(String)
    income_range = Column(String)
    location = Column(String)
    health_status = Column(String)
    ethnicity = Column(String)
    legal_status = Column(String)
    religion = Column(String)
    marital_status = Column(String)
    big_five_ocean_profile = Column(String)
    enneagram_profile = Column(String)
    mbti_profile = Column(String)
    personal_values = Column(String)
    hobbies = Column(String)
    llm_persona = Column(String)
    llm_typical_day = Column(Text)
    
    interactions = relationship("Interaction", back_populates="profile")


class Interaction(Base):
    __tablename__ = 'interactions'
    
    interaction_id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    profile_id = Column(Integer, ForeignKey('profiles.id'))
    query_text = Column(Text)
    answer_text = Column(Text)
    query_cost = Column(Integer)
    template_id = Column(Integer, ForeignKey('query_templates.id'))
    interaction_timestamp = Column(DateTime)
    project_survey_id = Column(Integer)
    
    profile = relationship("Profile", back_populates="interactions")
    query_template = relationship("QueryTemplate", back_populates="interactions")


# DataAccessLayer Implementation

class DataAccessLayer:
    def __init__(self):
        """
        Initializes the DataAccessLayer by setting up the database connection.
        """
        try:
            self.engine = create_engine(Config.SQLALCHEMY_DATABASE_URI, echo=False)
            self.Session = sessionmaker(bind=self.engine)
            #logger.info("Database connection established.")
        except SQLAlchemyError as e:
            logger.error(f"Error connecting to the database: {e}")
            self.engine = None
            self.Session = None
        self.current_survey_id = None
        self.session = None  # Initialize session attribute

    def get_session(self):
        """
        Returns the current session or creates a new one if none exists.
        """
        if not self.session:
            self.session = self.Session()
        return self.session

    def close_session(self):
        """
        Closes the current database session if it exists.
        """
        if self.session:
            self.session.close()
            self.session = None

    def get_survey_data(self, survey_id):
        """
        Fetches survey data including questions and their associated answer schemas.
        """
        if not self.engine:
            logger.error("No database connection.")
            return None

        self.current_survey_id = survey_id
        session = self.get_session()
        try:
            # Fetch interactions related to the survey
            interactions = session.query(Interaction).filter(
                Interaction.project_survey_id == survey_id
            ).all()

            if not interactions:
                logger.warning(f"No interactions found for survey ID: {survey_id}")
                return None

            # Extract unique query_template IDs from interactions
            template_ids = set(interaction.template_id for interaction in interactions)

            # Fetch corresponding QueryTemplates
            query_templates = session.query(QueryTemplate).filter(
                QueryTemplate.id.in_(template_ids)
            ).all()

            if not query_templates:
                logger.warning(f"No query templates found for survey ID: {survey_id}")
                return None

            # Structure the survey data
            survey_data = {
                'survey_id': survey_id,
                'questions': []
            }

            for qt in query_templates:
                question = {
                    'question_id': qt.id,
                    'question_text': qt.query_text,
                    'answer_schema': qt.schema
                }
                survey_data['questions'].append(question)

            logger.info(f"Fetched survey data for survey ID: {survey_id}")
            return survey_data

        except SQLAlchemyError as e:
            logger.error(f"Error fetching survey data: {e}")
            return None

    def get_question_data(self, question_id):
        """
        Fetches all responses for a specific question within the current survey.
        """
        if not self.engine:
            logger.error("No database connection.")
            return None

        if not self.current_survey_id:
            logger.error("Survey ID not set. Please fetch survey data first.")
            return None

        session = self.get_session()
        try:
            # Fetch interactions for the specific question within the current survey
            interactions = session.query(Interaction).filter(
                Interaction.project_survey_id == self.current_survey_id,
                Interaction.template_id == question_id
            ).all()
            '''
            print ('\n\nInteraction data for Q'+str(question_id))
            for interaction in interactions:
                print(f'Interaction ID: {interaction.interaction_id}')
                print(f'  Query Text: {interaction.query_text}')
                print(f'  Answer Text: {interaction.answer_text}')
                print(f'  Template ID: {interaction.template_id}')
                print('---')
            '''
            
            if not interactions:
                logger.warning(f"No responses found for question ID: {question_id} in survey ID: {self.current_survey_id}")
                return []

            # Parse the answer_text JSON strings into dictionaries
            responses = []
            for interaction in interactions:
                try:
                    answer = json.loads(interaction.answer_text)
                    responses.append(answer)
                except json.JSONDecodeError as e:
                    logger.error(f"Error decoding JSON for interaction ID {interaction.interaction_id}: {e}")
                    continue  # Skip malformed JSON entries

            #logger.info(f"Fetched {len(responses)} responses for question ID: {question_id}")
            return responses

        except SQLAlchemyError as e:
            logger.error(f"Error fetching question data: {e}")
            return None

    def get_analysis_methods_for_schema(self, schema_name):
        """
        Fetches analysis methods applicable to a given answer schema.
        """
        session = self.get_session()
        try:
            # Query the AnalysisMethodAnswerSchema table for enabled mappings
            mappings = session.query(AnalysisMethodAnswerSchema).filter(
                AnalysisMethodAnswerSchema.answer_schema == schema_name,
                AnalysisMethodAnswerSchema.enabled == True
            ).all()
            analysis_method_ids = {mapping.analysis_method_id for mapping in mappings if mapping.analysis_method_id is not None}
            methods = session.query(AnalysisMethod).filter(
                AnalysisMethod.id.in_(analysis_method_ids)
            ).all()
            #print([method.analysis_method for method in methods])
            return methods

        except SQLAlchemyError as e:
            logger.error(f"Error fetching analysis methods for schema '{schema_name}': {e}")
            return []
        finally:
            self.close_connection()

    def get_question_template(self, question_id):
        """
        Fetches the question template for a given question ID.
        """
        session = self.get_session()
        try:
            question = session.query(QueryTemplate).filter(
                QueryTemplate.id == question_id
            ).one_or_none()
            return question
        except SQLAlchemyError as e:
            logger.error(f"Error fetching question template for ID '{question_id}': {e}")
            return None

    def get_analysis_method_by_name(self, method_class_name):
        """
        Fetches an AnalysisMethod by its name.
        """
        session = self.get_session()
        try:
            #print('PARAMETER='+str(method_name)+".")
            method_data = session.query(AnalysisMethod).filter(
                AnalysisMethod.class_name == method_class_name
            ).one_or_none()
            
            return method_data
        except SQLAlchemyError as e:
            logger.error(f"Error fetching AnalysisMethod for name '{method_name}': {e}")
            return None

    def close_connection(self):
        """
        Closes the database connection gracefully.
        """
        self.close_session()
        if self.engine:
            self.engine.dispose()
            #logger.info("Database connection closed.")