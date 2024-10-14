from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Table  # Ensure 'Table' is imported
from sqlalchemy.orm import relationship, Session
from sqlalchemy.ext.declarative import declarative_base
import datetime

# Initialize the Base for SQLAlchemy models
Base = declarative_base()

# Association table for many-to-many relationship
survey_template_query_template = Table(
    'survey_template_query_template', Base.metadata,
    Column('survey_template_id', Integer, ForeignKey('survey_templates.id', ondelete="CASCADE"), primary_key=True),
    Column('query_template_id', Integer, ForeignKey('query_templates.id', ondelete="CASCADE"), primary_key=True)
)

class SurveyQueryParameter(Base):
    __tablename__ = 'survey_query_parameters'

    id = Column(Integer, primary_key=True)
    survey_template_id = Column(Integer, ForeignKey('survey_templates.id', ondelete="CASCADE"))
    query_template_id = Column(Integer, ForeignKey('query_templates.id', ondelete="CASCADE"))
    parameter_name = Column(String(255), nullable=False) 
    parameter_value = Column(String(255), nullable=False)
    survey_template = relationship("SurveyTemplate", backref="query_parameters")
    query_template = relationship("QueryTemplate", backref="survey_parameters")

class QueryTemplate(Base):
    __tablename__ = 'query_templates'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(String, nullable=True)
    schema = Column(Text, nullable=False)
    customizable_parameters = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    def __repr__(self):
        return f"<QueryTemplate(id={self.id}, name={self.name})>"

class SurveyTemplate(Base):
    __tablename__ = 'survey_templates'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Many-to-Many relationship with QueryTemplate
    query_templates = relationship(
        'QueryTemplate', secondary=survey_template_query_template, backref="survey_templates"
    )

    def __init__(self, name, description, query_templates=None):
        self.name = name
        self.description = description
        self.query_templates = query_templates or []

    def add_query_template(self, query_template):
        """Dynamically add a query template to the survey template."""
        self.query_templates.append(query_template)

    def save_to_db(self, session: Session):
        """Save the survey template along with its associated query templates."""
        session.add(self)
        session.commit()

    def __repr__(self):
        return f"<SurveyTemplate(id={self.id}, name={self.name})>"

class QueryTemplateManager:
    def __init__(self, session: Session, template_id=None, name=None, description=None, schema=None, customizable_parameters=None):
        self.session = session
        self.id = template_id
        self.name = name
        self.description = description
        self.schema = schema
        self.customizable_parameters = customizable_parameters  # New attribute for customizable parameters

    def save_to_db(self):
        """Save the template to the database."""
        template_record = QueryTemplate(
            name=self.name,
            description=self.description,
            schema=self.schema,
            customizable_parameters=self.customizable_parameters  # Save customizable parameters to the database
        )
        self.session.add(template_record)
        self.session.commit()
        self.id = template_record.id  # Update the template ID with the newly saved ID
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
                customizable_parameters=template_record.customizable_parameters  # Retrieve customizable parameters
            )
        return None

    @classmethod
    def get_all_templates(cls, session):
        """Retrieve all templates."""
        template_records = session.query(QueryTemplate).all()
        return [cls(session, tr.id, tr.name, tr.description, tr.schema, tr.customizable_parameters) for tr in template_records]
