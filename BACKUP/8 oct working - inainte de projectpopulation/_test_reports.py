from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models_view import CompletedSurvey, CompletedSurveyQuestion
from typing import Dict, List
from answer_schema import ANALYSIS_METHODS

# Database connection
DATABASE_URL = "postgresql://postgres:the bad zone@localhost/postgres"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def get_completed_surveys(session, project_id: int) -> List[CompletedSurvey]:
    return session.query(CompletedSurvey).filter_by(project_id=project_id).all()

def get_survey_questions(session, project_survey_id: int) -> List[CompletedSurveyQuestion]:
    return session.query(CompletedSurveyQuestion).filter_by(project_survey_id=project_survey_id).all()

def get_view_name(schema: str) -> str:
    schema_to_view = {
        "ScaleSchema": "vw_scale_responses",
        "OpenEndedSchema": "vw_open_ended_responses",
        "MultipleChoiceSchema": "vw_multiple_choice_responses",
        "YesNoSchema": "vw_yes_no_responses",
        "RankingSchema": "vw_ranking_responses"
    }
    return schema_to_view.get(schema, "Unknown")

def analyze_project(project_id: int):
    session = Session()
    try:
        completed_surveys = get_completed_surveys(session, project_id)
        
        if not completed_surveys:
            print(f"No completed surveys found for project ID {project_id}")
            return

        print(f"Completed surveys for project ID {project_id}:")
        for survey in completed_surveys:
            print(f"\nSurvey ID: {survey.project_survey_id}, Alias: {survey.survey_alias}")
            questions = get_survey_questions(session, survey.project_survey_id)
            
            for question in questions:
                print(f"  Question Template ID: {question.question_template_id}")
                print(f"  Answer Schema: {question.answer_schema}")
                print(f"  Database View: {get_view_name(question.answer_schema)}")
                print("  Available Analysis Methods:")
                for method in ANALYSIS_METHODS.get(question.answer_schema, []):
                    print(f"    - {method['name']}: {method['description']}")
                    print(f"      Chart Type: {method['chart_type']}")
                print()
    finally:
        session.close()

if __name__ == "__main__":
    project_id = int(input("Enter the project ID: "))
    analyze_project(project_id)