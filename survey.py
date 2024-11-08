#survey.py
"""
Core survey execution module.
Handles survey filtering, execution, progress tracking, and result processing using Celery tasks.
"""

from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import create_engine, text
from filter import Filter
from models import ProfileModel, SurveyTemplate, Interaction, Project, ProjectSurvey, FilterModel
from config import Config
from datetime import datetime
from celery import chord, shared_task
from celery_app import celery
from profile import Profile
import redis
from vector_utils import VectorSearch


def collect_results(result_parameters):
    """Save survey interactions to database and update completion status."""
    
    # Step 1: Create a database session using config details
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Step 2: Iterate over the extracted result parameters
        for result in result_parameters:
            interaction = Interaction(
                user_id=result['user_id'],
                profile_id=result['profile_id'],
                query_text=result['query_text'],
                answer_text=result['answer_text'],
                query_cost=result['query_cost'],
                template_id=result['template_id'],
                project_survey_id=result['project_survey_id'],
                interaction_timestamp=datetime.utcnow()
            )

            print('*** '+str(result)+' ***')
            # Step 3: Add the interaction to the session
            session.add(interaction)

            # Step 4: Update the completion percentage for the project survey to 100%
            project_survey = session.query(ProjectSurvey).filter_by(id=result['project_survey_id']).first()
            if project_survey:
                project_survey.completion_percentage = 100
                session.add(project_survey)

        # Step 5: Commit the session to save all interactions and updates in the database
        session.commit()
        print(f"Successfully saved {len(result_parameters)} interactions and updated completion percentages.")

    except Exception as e:
        # Rollback if any error occurs
        session.rollback()
        print(f"Error occurred while saving interactions: {e}")

    finally:
        # Close the session
        session.close()


@shared_task(name='survey.process_survey_results')
def process_survey_results(results):
    """ Celery task to process survey responses and save interactions. """
    # Initialize a list to store the parameters for each result
    result_parameters = []

    for result in results:
        # unpack the values based on their position
        answer_text, prompt_tokens, completion_tokens, user_id, profile_id, query_template_id, query_text, project_survey_id = result

        query_cost = prompt_tokens + completion_tokens

        # Append the parameters to the list
        result_parameters.append({
            'user_id': user_id,
            'profile_id': profile_id,
            'query_text': query_text,
            'answer_text': answer_text,
            'query_cost': query_cost,
            'template_id': query_template_id,
            'project_survey_id': project_survey_id 
        })

        print(f"Processed result for profile {profile_id}: query='{query_text}', answer='{answer_text}'")
        
    # Call collect_results to save the interactions
    collect_results(result_parameters)
    
    return result_parameters

class Survey:
    """ Survey execution manager handling profile filtering and distributed surveying. """
    def __init__(self, filter_obj: Filter, session: Session, survey_template: SurveyTemplate, 
                 custom_parameters_dict: dict = None, max_respondents: int = None):
        self.filter = filter_obj
        self.session = session
        self.survey_template = survey_template
        self.custom_parameters_dict = custom_parameters_dict or {}
        self.max_respondents = max_respondents
        self.vector_search = VectorSearch()  # Initialize VectorSearch

    def get_filtered_profiles(self, project_survey_id=None):
        # Get project survey and associated project/population
        project_survey = self.session.query(ProjectSurvey).filter_by(id=project_survey_id).first()
        project = self.session.query(Project).filter_by(id=project_survey.project_id).first()
        population = project.population

        # Start with base query
        query = self.session.query(ProfileModel)
        
        # Filter by population tag
        query = query.filter(ProfileModel.tags.contains(population.tag))
        
        # Apply standard filters
        query = self.filter.apply_filters(query)
        
        # Get the filter model to check for AI filter
        filter_model = self.session.query(FilterModel).filter_by(id=project_survey.segment_id).first()
        
        # If there's an AI filter, apply vector search
        if filter_model and filter_model.ai_filter:
            profile_ids = self.vector_search.find_similar_profiles_from_query(
                query=filter_model.ai_filter,
                base_query=query,
                similarity_threshold=0.32  
            )
            # Filter the query to only include matched profiles
            if profile_ids:
                query = query.filter(ProfileModel.id.in_(profile_ids))
            else:
                # If no profiles match the AI filter, return empty list
                return []
        
        # Apply respondent limit
        if self.max_respondents is not None:
            query = query.limit(self.max_respondents)
        
        return query.all()

    def run_survey(self, project_survey_id=None):
        """Execute survey on filtered profiles after cleaning previous data."""
        
        cleanup_survey_data(project_survey_id)
        filtered_profiles = self.get_filtered_profiles(project_survey_id)
        return self._survey_profiles(filtered_profiles, project_survey_id=project_survey_id)

    def _survey_profiles(self, filtered_profiles, project_survey_id=None):
        r = redis.Redis(host=Config.REDIS_HOST, port=Config.REDIS_PORT, db=Config.REDIS_DB)
        
        query_templates = self.survey_template.query_templates
        task_group = []
        total_tasks = len(filtered_profiles) * len(query_templates)
        
        # Set the total number of tasks in Redis and reset completed tasks
        r.set(f"survey_total_tasks_{project_survey_id}", total_tasks)
        r.set(f"survey_completed_tasks_{project_survey_id}", 0)
        
        # Retrieve the user_id associated with the project
        project_survey = self.session.query(ProjectSurvey).filter_by(id=project_survey_id).first()
        project = self.session.query(Project).filter_by(id=project_survey.project_id).first()
        user_id = project.user_id
        for profile_model in filtered_profiles:
            profile = Profile.from_model(self.session, profile_model)
            for query_template in query_templates:
                # Enqueue the query
                task = profile.enqueue_query(
                    user_id=user_id,
                    profile_id=profile_model.id,
                    query=query_template.query_text,
                    schema=query_template.schema,
                    query_template_id=query_template.id,
                    project_survey_id=project_survey_id  
                )
                task_group.append(task)
                print(f"Profile ID: {profile_model.id}, Name: {profile_model.profile_name}")
                print(f"Queued task for query template '{query_template.name}'")
        batch = chord(task_group)(celery.signature('survey.process_survey_results'))
        print('\n\nchord: ' + str(batch.id))
        return f"{len(filtered_profiles)} profiles surveyed with {len(query_templates)} query templates."
        
        
def get_survey_progress(project_survey_id):
    """Calculate survey completion percentage from Redis task counters."""
    
    r = redis.Redis(host=Config.REDIS_HOST, port=Config.REDIS_PORT, db=Config.REDIS_DB)
    total_tasks_raw = r.get(f"survey_total_tasks_{project_survey_id}")
    
    if total_tasks_raw is None:  # Survey hasn't started yet
        return None
        
    total_tasks = int(total_tasks_raw)
    completed_tasks = int(r.get(f"survey_completed_tasks_{project_survey_id}") or 0)
    
    if total_tasks == 0:
        return 0
    
    progress = (completed_tasks / total_tasks) * 100
    return round(progress, 2)
     
def cleanup_survey_data(project_survey_id):
    """Remove previous survey data using stored procedure."""
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    session = sessionmaker(bind=engine)()
    session.execute(text(f"CALL sp_cleanup_survey_data({project_survey_id});"))
    session.commit()
    session.close()