from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from filter import Filter  
from survey import Survey  
from models import SurveyTemplate 
from profile import Profile 

DATABASE_URL = "postgresql://postgres:the bad zone@localhost/postgres" 
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

# Load the survey template with ID 2 from the database
saved_template = session.query(SurveyTemplate).filter_by(id=2).first()

# Create a filter object
filter_obj = Filter(
    gender=["Female"],
    age_interval=(35, 40),
)

custom_params = {'PRODUCT/SERVICE': 'Smartphone', 'PRICE INCREASE PERCENTAGE': '10', 'FEATURE':'5G','PRODUCT/SERVICE DESCRIPTION':'This phone has a bright, clear display and a fast processor, making it quick and smooth to use. It comes with a great camera that takes high-quality photos, even in low light. The battery lasts longer, and it works with 5G for faster internet speeds. It also supports magnetic accessories and runs on the latest software, which includes new features like more privacy options and customizable screens. You can choose from different colors and storage sizes to fit your needs.'}

survey = Survey(filter_obj, session, saved_template, custom_parameters_dict=custom_params) 
result = survey.run_survey()

