from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import db, Project,  ProfileModel, FilterModel, SurveyTemplate, ProjectSurvey, Population
from filter_utils import populate_filter_form_choices, apply_filters_to_query, create_segment_from_form
from filter import Filter
from forms import ProjectForm, SegmentCreationForm
from flask_wtf.csrf import CSRFProtect
from config import Config
import redis
from sqlalchemy.orm import aliased
from survey import Survey, get_survey_progress

# Create a Blueprint for project-related routes
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
            total_profiles = ProfileModel.query.filter(ProfileModel.tags.contains(current_population.tag)).count()

    segments = FilterModel.query.filter_by(project_id=project.id).all()
    form = SegmentCreationForm()
    #survey_templates = SurveyTemplate.query.all()
    survey_templates = SurveyTemplate.query.filter_by(user_id=current_user.id).all()
    
    FilterAlias = aliased(FilterModel)
   
    project_surveys = db.session.query(ProjectSurvey)\
        .outerjoin(FilterAlias, ProjectSurvey.segment_id == FilterAlias.id)\
        .filter(ProjectSurvey.project_id == project_id)\
        .order_by(ProjectSurvey.survey_alias.asc())\
        .all()
        
    for survey in project_surveys:
        segment = db.session.query(FilterModel).filter_by(id=survey.segment_id).first()
        survey.segment_alias = segment.alias if segment else None
  
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
    form = SegmentCreationForm()

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

    # If form validation fails, re-render the dashboard with errors
    # We need to fetch all the data needed for the dashboard template
    projects = Project.query.filter_by(user_id=current_user.id, status='active').all()
    populations = Population.query.all()
    total_profiles = ProfileModel.query.filter(ProfileModel.tags.contains(project_population.population_tag)).count() if project_population else 0
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
    project = Project.query.filter_by(id=project_id, user_id=current_user.id).first_or_404()
    segment = FilterModel.query.filter_by(id=segment_id, project_id=project.id).first_or_404()

    db.session.delete(segment)
    db.session.commit()

    flash(f"Segment '{segment.alias}' has been removed.", "success")
    return redirect(url_for('projects_bp.project_dashboard', project_id=project_id))
    
@projects_bp.route('/project/<int:project_id>/create_survey', methods=['POST'])
@login_required
def create_survey(project_id):
    survey_alias = request.form.get('survey_alias')
    template_id = request.form.get('template_id')
    segment_id = request.form.get('segment_id')

    # Ensure the segment_id is provided
    if not segment_id:
        flash('You must select a population segment.', 'warning')
        return redirect(url_for('projects_bp.project_dashboard', project_id=project_id))

    # Check if a survey with the same template and segment already exists for this project
    existing_survey = ProjectSurvey.query.filter_by(
        project_id=project_id,
        survey_template_id=template_id,
        segment_id=segment_id
    ).first()

    if existing_survey:
        flash('A survey with the same template and segment already exists for this project.', 'warning')
    else:
        # Create the new survey and set completion_percentage to 0
        new_survey = ProjectSurvey(
            project_id=project_id,
            survey_template_id=template_id,
            survey_alias=survey_alias,
            segment_id=segment_id
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

    # Step 4: Prepare custom parameters (can be customized or fetched based on survey requirements)
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

    # Step 5: Run the survey using the Survey class
    survey = Survey(applied_filter, db.session, survey_template, custom_parameters_dict=custom_params)
    result = survey.run_survey(project_survey_id=survey_id)
    
    
    # Step 6: Provide feedback and redirect to the project dashboard
    flash(f'Survey "{project_survey.survey_alias}" has been queued...', 'success')
    return redirect(url_for('projects_bp.project_dashboard', project_id=project_id))


@projects_bp.route('/survey_progress/<int:project_survey_id>', methods=['GET'])
@login_required
def survey_progress(project_survey_id):
    progress = get_survey_progress(project_survey_id)
    rounded_progress = round(progress / 5) * 5
    
    return jsonify({
        'progress': int(rounded_progress)
    })
    
        
@projects_bp.route('/project/<int:project_id>/available_results', methods=['GET'])
@login_required
def available_results(project_id):
    project = Project.query.filter_by(id=project_id, user_id=current_user.id).first_or_404()
    completed_surveys = db.session.query(ProjectSurvey).filter(
        ProjectSurvey.project_id == project_id,
        ProjectSurvey.completion_percentage == 100
    ).all()
    
    project_population = None
    if project.population_id:
        project_population = Population.query.filter_by(id=project.population_id).first()

    return render_template('_available_results.html', 
                           completed_surveys=completed_surveys, 
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