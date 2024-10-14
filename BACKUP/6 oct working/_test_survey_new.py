from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from filter import Filter  
from survey import Survey  
from models import SurveyTemplate, ProjectSurvey, Project, FilterModel, ProfileModel  # Assuming ProfileModel is needed for querying profiles
from sqlalchemy.dialects import postgresql

DATABASE_URL = "postgresql://postgres:the bad zone@localhost/postgres"  
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

# Step 1: Select the first survey available for the project called "Project 1"
project = session.query(Project).filter_by(name="al doilea proiect").first()

if not project:
    raise Exception("Project not found")

# Get the first available survey for this project
project_survey = session.query(ProjectSurvey).filter_by(project_id=project.id).first()

if not project_survey:
    raise Exception(f"No surveys found for project {project.name}")

# Step 2: Apply the filter corresponding to the segment_id from the Filters table
filter_model = session.query(FilterModel).filter_by(id=project_survey.segment_id).first()
if not filter_model:
    raise Exception(f"Filter with ID {project_survey.segment_id} not found")

# Use the from_model method to create a Filter object
applied_filter = Filter.from_model(filter_model)

# Step 3: Load the survey template associated with the project survey
saved_template = session.query(SurveyTemplate).filter_by(id=project_survey.survey_template_id).first()

if not saved_template:
    raise Exception(f"Survey template with ID {project_survey.survey_template_id} not found")

# Step 4: Define custom parameters
custom_params = {
    'PRODUCT/SERVICE': 'Smartphone', 
    'PRICE INCREASE PERCENTAGE': '10', 
    'FEATURE': '5G',
    'PRODUCT/SERVICE DESCRIPTION': (
        'This phone has a bright, clear display and a fast processor, making it quick and smooth to use. '
        'It comes with a great camera that takes high-quality photos, even in low light. The battery lasts longer, '
        'and it works with 5G for faster internet speeds. It also supports magnetic accessories and runs on the '
        'latest software, which includes new features like more privacy options and customizable screens. '
        'You can choose from different colors and storage sizes to fit your needs.'
    )
}

# Step 5: Prepare the query to get profiles, apply filters, and print the final query
query = session.query(ProfileModel)

# Apply filters using the apply_filters method from the Filter class
filtered_query = applied_filter.apply_filters(query)

# Print the final SQL query for debugging purposes
print(filtered_query.statement.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}))

profiles = filtered_query.all()
print(profiles)  # This will show the profiles after filtering

# Step 6: Run the survey with the applied filter and project_survey_id
survey = Survey(applied_filter, session, saved_template, custom_parameters_dict=custom_params) 
# result = survey.run_survey(project_survey.id)  # Uncomment this to run the survey
# print(result)
