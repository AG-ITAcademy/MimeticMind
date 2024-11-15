#projects.py

"""
Project management routes and functionality for the survey application.
This module handles all project-related operations including:
- Project creation, viewing, and management
- Population assignment and segment definition
- Survey creation and execution within projects 
- Progress tracking and result management
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from markupsafe import Markup
from flask_login import login_required, current_user
from models import db, Project,  FilterModel, SurveyTemplate, ProjectSurvey, Population, ProfileView
from filter_utils import populate_filter_form_choices, create_segment_from_form
from filter import Filter
from forms import ProjectForm,  FilterForm
from flask_wtf.csrf import CSRFProtect
from sqlalchemy.orm import aliased
from vector_utils import VectorSearch
from survey import Survey, get_survey_progress


# Blueprint for project-related routes
projects_bp = Blueprint('projects_bp', __name__)
csrf = CSRFProtect()

@projects_bp.route('/projects/<int:project_id>')
@login_required
def project_dashboard(project_id):
    project = Project.query.filter_by(id=project_id, user_id=current_user.id).first_or_404()
    projects = Project.query.filter_by(user_id=current_user.id, status='active').all()
    
    populations = Population.query.all()
    
    project_population = None
    total_profiles = 0
    if project.population_id:
        current_population = Population.query.filter_by(id=project.population_id).first()
        if current_population:
            project_population = type('ProjectPopulation', (), {
                'population_tag': current_population.tag,
                'population': current_population
            })()
            total_profiles = ProfileView.query.filter(ProfileView.tags.contains(current_population.tag)).count()

    segments = FilterModel.query.filter_by(project_id=project.id).all()

    # calculate the number of profiles in each segment
    for segment in segments:
        filter_obj = Filter.from_model(segment)
        base_query = ProfileView.query
        if project_population:
            base_query = base_query.filter(ProfileView.tags.contains(project_population.population_tag))
        filtered_query = filter_obj.apply_filters(base_query)
        segment.total_profiles = filtered_query.count()
        
    form = FilterForm()

    survey_templates = SurveyTemplate.query.filter_by(user_id=current_user.id).all()
    
    FilterAlias = aliased(FilterModel)
   
    project_surveys = db.session.query(ProjectSurvey)\
        .outerjoin(FilterAlias, ProjectSurvey.segment_id == FilterAlias.id)\
        .filter(ProjectSurvey.project_id == project_id)\
        .order_by(ProjectSurvey.id.asc())\
        .all()
        
    for survey in project_surveys:
        segment = db.session.query(FilterModel).filter_by(id=survey.segment_id).first()
        survey.template = db.session.query(SurveyTemplate.name).filter_by(id=survey.survey_template_id).scalar()
        survey.segment_alias = segment.alias if segment else None
        survey.is_running = (survey.completion_percentage == 0)
  
    completed_surveys = db.session.query(ProjectSurvey).filter(
        ProjectSurvey.project_id == project_id,
        ProjectSurvey.completion_percentage == 100
    ).all()

    if project_population:
        populate_filter_form_choices(form, project_population.population_tag)

    return render_template(
        'project_dashboard.html', 
        project=project, 
        projects=projects, 
        project_population=project_population,
        populations=populations,
        total_profiles=total_profiles,
        form=form,
        segments=segments,
        survey_templates=survey_templates,
        project_surveys=project_surveys,
        completed_surveys=completed_surveys
    )

# Create a project route
@projects_bp.route('/create-project', methods=['GET', 'POST'])
@login_required
def create_project():
    form = ProjectForm()

    active_projects_count = Project.query.filter_by(user_id=current_user.id, status='active').count()
    if active_projects_count >= current_user.subscription.max_projects:
        upgrade_button = Markup('<a href="{}" class="btn btn-sm btn-primary">Upgrade Plan</a>'.format(url_for('pricing')))
        flash(Markup(f"You have reached the maximum number of projects ({current_user.subscription.max_projects}) allowed for your subscription tier. Please upgrade your plan to create more projects. {upgrade_button}"), "warning")
        return redirect(url_for('dashboard_bp.dashboard'))  

    if form.validate_on_submit():
        new_project = Project(
            name=form.name.data,
            description=form.description.data,
            user_id=current_user.id,
            population_id=None
        )
        db.session.add(new_project)
        db.session.commit()
        
        flash("New project created successfully!", "success")
        return redirect(url_for('dashboard_bp.dashboard'))

    return render_template('create_project.html', form=form)

# Apply population route
@projects_bp.route('/projects/<int:project_id>/apply_population', methods=['POST'])
@login_required
def apply_population(project_id):
    project = Project.query.filter_by(id=project_id, user_id=current_user.id).first_or_404()
    population_tag = request.form.get('population_tag')

    if not population_tag:
        flash("Please select a population.", "warning")
        return redirect(url_for('projects_bp.project_dashboard', project_id=project_id))

    population = Population.query.filter_by(tag=population_tag).first_or_404()
    
    project.population_id = population.id
    db.session.commit()

    flash(f"Population '{population.name}' has been set for this project.", "success")
    return redirect(url_for('projects_bp.project_dashboard', project_id=project_id))

@projects_bp.route('/projects/<int:project_id>/define_segments', methods=['POST'])
@login_required
def define_segments(project_id):
    project = Project.query.filter_by(id=project_id, user_id=current_user.id).first_or_404()
    form = FilterForm()

    project_population = None
    if project.population_id:
        current_population = Population.query.filter_by(id=project.population_id).first()
        if current_population:
            project_population = type('ProjectPopulation', (), {
                'population_tag': current_population.tag,
                'population': current_population
            })()

    # Populate form choices based on the selected population
    if project_population:
        populate_filter_form_choices(form, project_population.population_tag)

    if form.validate_on_submit():
        new_filter = create_segment_from_form(project.id, form.data)
        flash('Segment created successfully!', 'success')
        return redirect(url_for('projects_bp.project_dashboard', project_id=project_id))
    else:
        print("Form validation failed:", form.errors)

    projects = Project.query.filter_by(user_id=current_user.id, status='active').all()
    populations = Population.query.all()
    total_profiles = ProfileView.query.filter(ProfileView.tags.contains(project_population.population_tag)).count() if project_population else 0
    segments = FilterModel.query.filter_by(project_id=project.id).all()
    survey_templates = SurveyTemplate.query.all()
    project_surveys = ProjectSurvey.query.filter_by(project_id=project_id).order_by(ProjectSurvey.survey_alias.asc()).all()
    completed_surveys = db.session.query(ProjectSurvey).filter(
        ProjectSurvey.project_id == project_id,
        ProjectSurvey.completion_percentage == 100
    ).all()

    return render_template(
        'project_dashboard.html', 
        project=project,
        projects=projects,
        project_population=project_population,
        populations=populations,
        total_profiles=total_profiles,
        form=form,
        segments=segments,
        survey_templates=survey_templates,
        project_surveys=project_surveys,
        completed_surveys=completed_surveys
    )


@projects_bp.route('/projects/<int:project_id>/remove_segment/<int:segment_id>', methods=['POST'])
@login_required
def remove_segment(project_id, segment_id):
    try:
        project = Project.query.filter_by(id=project_id, user_id=current_user.id).first_or_404()
        segment = FilterModel.query.filter_by(id=segment_id, project_id=project.id).first_or_404()
        surveys_count = ProjectSurvey.query.filter_by(segment_id=segment_id).count()
        db.session.begin_nested()
        ProjectSurvey.query.filter_by(segment_id=segment_id).delete()

        db.session.delete(segment)
        db.session.commit()
        
        if surveys_count > 0:
            flash(f"Segment '{segment.alias}' and its {surveys_count} associated surveys have been removed.", "success")
        else:
            flash(f"Segment '{segment.alias}' has been removed.", "success")
            
        return redirect(url_for('projects_bp.project_dashboard', project_id=project_id))
        
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred while removing the segment: {str(e)}", "danger")
        return redirect(url_for('projects_bp.project_dashboard', project_id=project_id))
    
@projects_bp.route('/project/<int:project_id>/create_survey', methods=['POST'])
@login_required
def create_survey(project_id):
    template_id = request.form.get('template_id')
    template_name = db.session.query(SurveyTemplate.name).filter_by(id=template_id).scalar()
    segment_id = request.form.get('segment_id')
    segment_name = db.session.query(FilterModel.alias).filter_by(id=segment_id).scalar()
    survey_alias = template_name +' --> '+segment_name
    respondents = request.form.get('max_respondents', type=int)
   
    # Check if a survey with the same template and segment already exists for this project
    existing_survey = ProjectSurvey.query.filter_by(
        project_id=project_id,
        survey_template_id=template_id,
        segment_id=segment_id
    ).first()
 
    if existing_survey:
        flash('A survey with the same template and segment already exists for this project.', 'warning')
    else:
        # Create the new survey and set completion_percentage to null
        new_survey = ProjectSurvey(
            project_id=project_id,
            survey_template_id=template_id,
            survey_alias=survey_alias,
            segment_id=segment_id,
            respondents=respondents
        )
        db.session.add(new_survey)
        db.session.commit()
        flash('Survey created successfully!', 'success')

    return redirect(url_for('projects_bp.project_dashboard', project_id=project_id))

    
@projects_bp.route('/project/<int:project_id>/remove_survey/<int:survey_id>', methods=['POST'])
@login_required
def remove_survey(project_id, survey_id):
    survey = ProjectSurvey.query.get_or_404(survey_id)

    # Ensure that the survey belongs to the current project
    if survey.project_id == project_id:
        db.session.delete(survey)
        db.session.commit()
        flash('Survey removed successfully!', 'success')
    else:
        flash('Survey does not belong to this project.', 'danger')

    return redirect(url_for('projects_bp.project_dashboard', project_id=project_id))
    

@projects_bp.route('/project/<int:project_id>/run_survey/<int:survey_id>', methods=['POST'])
@login_required
def run_survey(project_id, survey_id):
    # Step 1: Retrieve the project and the survey
    project = Project.query.filter_by(id=project_id, user_id=current_user.id).first_or_404()
    project_survey = ProjectSurvey.query.filter_by(id=survey_id, project_id=project_id).first_or_404()
    
    # Set the completion_percentage to 0 to indicate that survey is running
    project_survey.completion_percentage = 0
    db.session.commit()
    
    # Step 2: Get the filter associated with the survey
    filter_model = FilterModel.query.filter_by(id=project_survey.segment_id).first_or_404()
    applied_filter = Filter.from_model(filter_model)
    
    # Step 3: Get the survey template associated with the project survey
    survey_template = SurveyTemplate.query.filter_by(id=project_survey.survey_template_id).first_or_404()
    
    # Step 4: Count respondents and calculate interactions
    query = db.session.query(ProfileView)
    query = query.filter(ProfileView.tags.contains(project.population.tag))
    filtered_query = applied_filter.apply_filters(query)
    
    if filter_model.ai_filter:
        # If there's an AI filter, check vector search results
        vector_search = VectorSearch()
        profile_ids = vector_search.find_similar_profiles_from_query(
            query=filter_model.ai_filter,
            base_query=filtered_query,
            similarity_threshold=0.32 # this will be customizable in the future
        )
        if not profile_ids:
            flash(f'No profiles match the AI filter criteria for survey "{project_survey.survey_alias}".', 'warning')
            return redirect(url_for('projects_bp.project_dashboard', project_id=project_id))
        filtered_query = filtered_query.filter(ProfileView.id.in_(profile_ids))
    
    # Add limit to the query before counting
    limited_query = filtered_query.limit(project_survey.respondents)
    respondents_count = limited_query.count()
    interactions_count = respondents_count * len(survey_template.query_templates)
    
    # Step 5: Check subscription limits
    if not current_user.subscription or not current_user.subscription.is_active:
        flash("No active subscription found", 'warning')
        return redirect(url_for('projects_bp.project_dashboard', project_id=project_id))
    
    active_projects = Project.query.filter_by(user_id=current_user.id, status='active').count()
    if active_projects > current_user.subscription.max_projects:
        flash(f"Project limit exceeded. Maximum allowed: {current_user.subscription.max_projects}", 'warning')
        return redirect(url_for('projects_bp.project_dashboard', project_id=project_id))
    
    if respondents_count > current_user.subscription.max_respondents_per_survey:
        flash(f"Respondents per survey limit exceeded. Maximum allowed: {current_user.subscription.max_respondents_per_survey}", 'warning')
        return redirect(url_for('projects_bp.project_dashboard', project_id=project_id))
    
    if interactions_count > current_user.subscription.remaining_interactions:
        flash(f"Insufficient interaction credits. Available: {current_user.subscription.remaining_interactions}", 'warning')
        return redirect(url_for('projects_bp.project_dashboard', project_id=project_id))
    
    # Deduct interactions from remaining_interactions
    current_user.subscription.remaining_interactions -= interactions_count
    db.session.commit()
    
    # Step 6: Run the survey using the Survey class and applying the max_respondents limit
    survey = Survey(applied_filter, db.session, survey_template, custom_parameters_dict={}, max_respondents=project_survey.respondents)
    result = survey.run_survey(project_survey_id=survey_id)
    
    # Step 7: Provide feedback and redirect to the project dashboard
    flash(f'Survey "{project_survey.survey_alias}" has been queued...', 'success')
    return redirect(url_for('projects_bp.project_dashboard', project_id=project_id))


@projects_bp.route('/survey_progress/<int:project_survey_id>', methods=['GET'])
@login_required
def survey_progress(project_survey_id):
    progress = get_survey_progress(project_survey_id)
    if progress is None:
        return jsonify({'progress': None})
        
    rounded_progress = round(progress / 5) * 5
    return jsonify({'progress': int(rounded_progress)})
    
        
@projects_bp.route('/project/<int:project_id>/available_results', methods=['GET'])
@login_required
def available_results(project_id):
    project = Project.query.filter_by(id=project_id, user_id=current_user.id).first_or_404()
    
    # Get both completed and in-progress surveys
    all_surveys = db.session.query(ProjectSurvey).filter(
        ProjectSurvey.project_id == project_id
    ).all()
    
    completed_surveys = [s for s in all_surveys if s.completion_percentage == 100]
    in_progress_surveys = [s for s in all_surveys if s.completion_percentage is not None 
                          and s.completion_percentage > 0 
                          and s.completion_percentage < 100]
    
    project_population = None
    if project.population_id:
        project_population = Population.query.filter_by(id=project.population_id).first()
        
    return render_template('_available_results.html', 
                         completed_surveys=completed_surveys,
                         in_progress_surveys=in_progress_surveys,
                         project_id=project_id,
                         project_population=project_population)
                           
@projects_bp.route('/projects/<int:project_id>/rename', methods=['POST'])
@login_required
def rename_project(project_id):
    project = Project.query.filter_by(id=project_id, user_id=current_user.id).first_or_404()
    
    new_name = request.json.get('new_name')
    if not new_name:
        return jsonify({'success': False, 'message': 'New name is required'}), 400
    
    project.name = new_name
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Project renamed successfully'})
