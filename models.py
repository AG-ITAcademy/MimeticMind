# models.py
from sqlalchemy import Column, Integer, Text, Numeric, ForeignKey, DateTime, String
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import uuid
from sqlalchemy.orm import Session , relationship

db = SQLAlchemy()

class Population(db.Model):
    __tablename__ = 'populations'
    
    tag = db.Column(db.String)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.Text)
    prompt_template = db.Column(db.JSON)
    main_language = db.Column(db.String)
    flag = db.Column(db.String)
    id = db.Column(db.Integer, primary_key=True)

class FilterModel(db.Model):
    __tablename__ = 'filters'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    alias = db.Column(db.String(255), nullable=False)  # Name/Alias for the segment
    gender = db.Column(db.String(50))
    age_min = db.Column(db.Integer)
    age_max = db.Column(db.Integer)
    location = db.Column(db.String(255))
    ethnicity = db.Column(db.String(255))
    occupation = db.Column(db.String(255))
    education_level = db.Column(db.String(255))
    religion = db.Column(db.String(255))
    health_status = db.Column(db.String(255))
    legal_status = db.Column(db.String(255))
    marital_status = db.Column(db.String(255))
    income_range = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    project = db.relationship('Project', backref=db.backref('filters', cascade="all, delete"))


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    google_id = db.Column(db.String(255), unique=True, nullable=False) 
    email = db.Column(db.String(255), nullable=False, unique=True)
    full_name = db.Column(db.String(255), nullable=True)
    profile_picture = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    password = db.Column(db.String(255), nullable=True) 
    is_confirmed = db.Column(db.Boolean, default=False)
    confirm_token = db.Column(db.String(100), nullable=True)
    
    def __repr__(self):
        return f'<User {self.email}>'

class ProfileModel(db.Model):
    __tablename__ = 'profiles'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    profile_name = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    version = db.Column(db.Float, default=1.0)
    tags = db.Column(db.String, default='')
    
    birth_date = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    education_level = db.Column(db.String(255), nullable=False)
    occupation = db.Column(db.String(255), nullable=False)
    income_range = db.Column(db.String(50), nullable=True)
    location = db.Column(db.String(255), nullable=False)
    health_status = db.Column(db.String(255), nullable=False)
    ethnicity = db.Column(db.String(255), nullable=False)
    legal_status = db.Column(db.String(255), nullable=False)
    religion = db.Column(db.String(255), nullable=False)
    marital_status = db.Column(db.String(255), nullable=False)

    big_five_ocean_profile = db.Column(db.String(5), nullable=True)
    enneagram_profile = db.Column(db.Integer, nullable=True)
    mbti_profile = db.Column(db.String(4), nullable=True)
    personal_values = db.Column(db.String, nullable=True)
    hobbies = db.Column(db.String, nullable=True)

    llm_persona = db.Column(db.Text, nullable=True)
    llm_typical_day = db.Column(db.Text, nullable=True)

    # Relationship to interactions
    interactions = relationship('Interaction', back_populates='profile')

# Define Interaction model
class Interaction(db.Model):
    __tablename__ = 'interactions'

    interaction_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    profile_id = Column(Integer, ForeignKey('profiles.id'), nullable=False)
    query_text = Column(Text, nullable=False)
    answer_text = Column(Text)
    query_cost = Column(Numeric)
    template_id = Column(Integer, ForeignKey('query_templates.id'), nullable=False)
    interaction_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    project_survey_id = Column(Integer, ForeignKey('query_templates.id'), nullable=True)
    
    # Relationships
    profile = relationship("ProfileModel", back_populates="interactions")
    
    # Specify foreign_keys to remove ambiguity
    query_template = relationship(
        "QueryTemplate",
        foreign_keys=[template_id],  # Foreign key to the main query template
    )
    
    project_survey_template = relationship(
        "QueryTemplate",
        foreign_keys=[project_survey_id],  # Foreign key for the project survey template
    )


# Project model
class Project(db.Model):
    __tablename__ = 'projects'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(10), nullable=False, default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    population_id = db.Column(db.Integer, db.ForeignKey('populations.id'), nullable=True)
    
    population = db.relationship('Population', backref='projects')
    project_surveys = db.relationship('ProjectSurvey', back_populates='project')

# Template models from template.py
survey_template_query_template = db.Table(
    'survey_template_query_template',
    db.Column('survey_template_id', db.Integer, db.ForeignKey('survey_templates.id', ondelete="CASCADE"), primary_key=True),
    db.Column('query_template_id', db.Integer, db.ForeignKey('query_templates.id', ondelete="CASCADE"), primary_key=True)
)


class SurveyQueryParameter(db.Model):
    __tablename__ = 'survey_query_parameters'

    id = db.Column(db.Integer, primary_key=True)
    survey_template_id = db.Column(db.Integer, db.ForeignKey('survey_templates.id', ondelete="CASCADE"))
    query_template_id = db.Column(db.Integer, db.ForeignKey('query_templates.id', ondelete="CASCADE"))
    parameter_name = db.Column(db.String(255), nullable=False) 
    parameter_value = db.Column(db.String(255), nullable=False)
    survey_template = db.relationship("SurveyTemplate", backref="query_parameters")
    query_template = db.relationship("QueryTemplate", backref="survey_parameters")

class QueryTemplate(db.Model):
    __tablename__ = 'query_templates'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False, default="New Survey")
    query_text = db.Column(db.String, nullable=True)
    schema = db.Column(db.Text, nullable=False)
    customizable_parameters = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    description = db.Column(db.String, nullable=True)
    def __repr__(self):
        return f"<QueryTemplate(id={self.id}, name={self.name})>"

class SurveyTemplate(db.Model):
    __tablename__ = 'survey_templates'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    context_prompt = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    query_templates = db.relationship('QueryTemplate', secondary=survey_template_query_template, backref="survey_templates")
    project_surveys = db.relationship('ProjectSurvey', back_populates='survey_template')
    
    def __init__(self, name="New Survey", description=None, context_prompt=None, user_id=None, query_templates=None):
        self.name = name
        self.description = description
        self.context_prompt = context_prompt
        self.user_id = user_id
        self.query_templates = query_templates or []

    def add_query_template(self, query_template):
        self.query_templates.append(query_template)

    def save_to_db(self, session):
        session.add(self)
        session.commit()

    def __repr__(self):
        return f"<SurveyTemplate(id={self.id}, name={self.name})>"
        
    
class ProjectSurvey(db.Model):
    __tablename__ = 'project_survey'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    survey_template_id = db.Column(db.Integer, db.ForeignKey('survey_templates.id'), nullable=False)
    survey_alias = Column(String, nullable=True)
    completion_percentage = Column(Integer, nullable=True)
    segment_id = db.Column(db.Integer, db.ForeignKey('filters.id'), nullable=False)
    
    project = db.relationship('Project', back_populates='project_surveys')
    survey_template = db.relationship('SurveyTemplate', back_populates='project_surveys')


class QueryTemplateManager:
    def __init__(self, session: Session, template_id=None, name=None, description=None, schema=None, customizable_parameters=None):
        self.session = session
        self.id = template_id
        self.name = name
        self.description = description
        self.schema = schema
        self.customizable_parameters = customizable_parameters  

    def save_to_db(self):
        """Save the template to the database."""
        template_record = QueryTemplate(
            name=self.name,
            description=self.description,
            schema=self.schema,
            customizable_parameters=self.customizable_parameters 
        )
        self.session.add(template_record)
        self.session.commit()
        self.id = template_record.id  
        return template_record.id

    @classmethod
    def get_by_id(cls, session, template_id):
        """Retrieve a template by its ID."""
        template_record = session.query(QueryTemplate).filter_by(id=template_id).first()
        if template_record:
            return cls(
                session=session,
                template_id=template_record.id,
                name=template_record.name,
                description=template_record.description,
                schema=template_record.schema,
                customizable_parameters=template_record.customizable_parameters  
            )
        return None

    @classmethod
    def get_all_templates(cls, session):
        """Retrieve all templates."""
        template_records = session.query(QueryTemplate).all()
        return [cls(session, tr.id, tr.name, tr.description, tr.schema, tr.customizable_parameters) for tr in template_records]