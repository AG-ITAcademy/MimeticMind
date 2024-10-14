from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from filter import Filter
from survey import Survey
from template import SurveyTemplate  
from profile import Profile

# Setup SQLAlchemy connection and session
DATABASE_URL = "postgresql://postgres:the bad zone@localhost/postgres"  
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

saved_template = session.query(SurveyTemplate).filter_by(id=1).first()

if not saved_template:
    print("Template with ID 1 not found.")
    exit()

filter_obj = Filter(
    gender=["Female"],
    age_interval=(35, 45),
    occupation=["Retired"]
)

query = "Tell me about your daily routine."
survey = Survey(filter_obj, session, saved_template, query)
result = survey.run_survey()

if isinstance(result, str) and result.startswith("Error"):
    print(result)
else:
    print(result)
