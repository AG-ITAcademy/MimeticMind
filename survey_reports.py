from flask import Blueprint, render_template
from models import db, Project, ProjectSurvey,  Population
from models_view import CompletedSurvey
from flask_login import login_required, current_user
from datetime import datetime

survey_reports_bp = Blueprint('survey_reports_bp', __name__)

@survey_reports_bp.route('/survey_reports')
@login_required
def survey_reports():
    # Get all active projects for the current user
    projects = Project.query.filter_by(
        user_id=current_user.id,
        status='active'
    ).all()
    
    # Create a dictionary to store project data with their surveys
    projects_data = []
    
    for project in projects:
        # Get all completed surveys for this project with their metadata
        completed_surveys = db.session.query(
            ProjectSurvey, CompletedSurvey
        ).join(
            CompletedSurvey,
            ProjectSurvey.id == CompletedSurvey.project_survey_id
        ).filter(
            ProjectSurvey.project_id == project.id,
            ProjectSurvey.completion_percentage == 100
        ).all()
        
        # Get project population if it exists
        project_population = None
        if project.population_id:
            project_population = Population.query.filter_by(id=project.population_id).first()
        
        # Add project and its surveys to the data structure
        project_info = {
            'project': project,
            'population': project_population,
            'surveys': completed_surveys
        }
        projects_data.append(project_info)
    
    return render_template('survey_reports.html', 
                         projects_data=projects_data,
                         now=datetime.utcnow())