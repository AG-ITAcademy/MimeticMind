from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import db, Project, ProjectPopulation, ProfileModel, FilterModel, SurveyTemplate, ProjectSurvey, Population
from forms import ProjectForm, FilterForm
from flask_wtf.csrf import CSRFProtect
from filter import Filter  
from config import Config
import redis
from survey import Survey, get_survey_progress,  get_survey_reload_flag, set_survey_reload_flag

# Create a Blueprint for project-related routes
projects_bp = Blueprint('projects_bp', __name__)
csrf = CSRFProtect()

# Project-specific dashboard route
@projects_bp.route('/projects/<int:project_id>')
@login_required
def project_dashboard(project_id):
    # Fetch the current project and all active projects for the user
    project = Project.query.filter_by(id=project_id, user_id=current_user.id).first_or_404()
    projects = Project.query.filter_by(user_id=current_user.id, status='active').all()
    
    # Fetch the ProjectPopulation record for this project
    project_population = ProjectPopulation.query.filter_by(project_id=project.id).first()
    
    # Fetch all available populations
    populations = Population.query.all()
    
    # Count the number of matching profiles based on the selected population
    total_profiles = 0
    if project_population:
        total_profiles = ProfileModel.query.filter(ProfileModel.tags.contains(project_population.population_tag)).count()

    # Retrieve all defined segments (filters) for the project
    segments = FilterModel.query.filter_by(project_id=project.id).all()

    # Initialize the form
    form = FilterForm()

    # Fetch all survey templates for the dropdown
    survey_templates = SurveyTemplate.query.all()
    
    # Fetch all surveys linked to this project
    project_surveys = ProjectSurvey.query.filter_by(project_id=project_id).order_by(ProjectSurvey.survey_alias.asc()).all()

    # Fetch completed surveys for this project
    completed_surveys = db.session.query(ProjectSurvey).filter(
        ProjectSurvey.project_id == project_id,
        ProjectSurvey.completion_percentage == 100
    ).all()

    # Fetch distinct values for form fields based on selected population
    if project_population:
        population_tag = project_population.population_tag
        query_filter = ProfileModel.tags.contains(population_tag)
        
        genders = db.session.query(ProfileModel.gender).filter(query_filter).distinct().all()
        locations = db.session.query(ProfileModel.location).filter(query_filter).distinct().all()
        ethnicities = db.session.query(ProfileModel.ethnicity).filter(query_filter).distinct().all()
        occupations = db.session.query(ProfileModel.occupation).filter(query_filter).distinct().all()
        education_levels = db.session.query(ProfileModel.education_level).filter(query_filter).distinct().all()
        religions = db.session.query(ProfileModel.religion).filter(query_filter).distinct().all()
        health_statuses = db.session.query(ProfileModel.health_status).filter(query_filter).distinct().all()
        legal_statuses = db.session.query(ProfileModel.legal_status).filter(query_filter).distinct().all()
        marital_statuses = db.session.query(ProfileModel.marital_status).filter(query_filter).distinct().all()

        # Set the choices for each field
        form.gender.choices = [('Any', 'Any')] + [(g[0], g[0]) for g in genders if g[0]]
        form.location.choices = [('Any', 'Any')] + [(l[0], l[0]) for l in locations if l[0]]
        form.ethnicity.choices = [('Any', 'Any')] + [(e[0], e[0]) for e in ethnicities if e[0]]
        form.occupation.choices = [('Any', 'Any')] + [(o[0], o[0]) for o in occupations if o[0]]
        form.education_level.choices = [('Any', 'Any')] + [(e[0], e[0]) for e in education_levels if e[0]]
        form.religion.choices = [('Any', 'Any')] + [(r[0], r[0]) for r in religions if r[0]]
        form.health_status.choices = [('Any', 'Any')] + [(h[0], h[0]) for h in health_statuses if h[0]]
        form.legal_status.choices = [('Any', 'Any')] + [(l[0], l[0]) for l in legal_statuses if l[0]]
        form.marital_status.choices = [('Any', 'Any')] + [(m[0], m[0]) for m in marital_statuses if m[0]]
    else:
        # If no population is selected, set empty choices
        form.gender.choices = [('Any', 'Any')]
        form.location.choices = [('Any', 'Any')]
        form.ethnicity.choices = [('Any', 'Any')]
        form.occupation.choices = [('Any', 'Any')]
        form.education_level.choices = [('Any', 'Any')]
        form.religion.choices = [('Any', 'Any')]
        form.health_status.choices = [('Any', 'Any')]
        form.legal_status.choices = [('Any', 'Any')]
        form.marital_status.choices = [('Any', 'Any')]

    # Add income range options to the form
    form.income_range.choices = [('Any', 'Any'), ('Low', 'Low'), ('Medium', 'Medium'), ('High', 'High')]

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
            user_id=current_user.id,  # Get the current logged-in user's ID
        )
        db.session.add(new_project)
        db.session.commit()
        
        flash("New project created successfully!", "success")
        return redirect(url_for('dashboard_bp.dashboard'))  # Redirect to the dashboard or projects list

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
    
    # Check if a ProjectPopulation record already exists for this project
    project_population = ProjectPopulation.query.filter_by(project_id=project.id).first()
    
    if project_population:
        # Update the existing record
        project_population.population_tag = population.tag
    else:
        # Create a new ProjectPopulation record
        project_population = ProjectPopulation(
            project_id=project.id,
            population_tag=population.tag
        )
        db.session.add(project_population)

    db.session.commit()

    flash(f"Population '{population.name}' has been set for this project.", "success")
    return redirect(url_for('projects_bp.project_dashboard', project_id=project_id))

@projects_bp.route('/projects/<int:project_id>/define_segments', methods=['POST'])
@login_required
def define_segments(project_id):
    project = Project.query.filter_by(id=project_id, user_id=current_user.id).first_or_404()
    form = FilterForm()

    # Replicate the form population logic to ensure consistency
    selected_population_tags = [tag[0] for tag in db.session.query(ProjectPopulation.population_tag).filter_by(project_id=project_id).distinct().all()]

    genders = db.session.query(ProfileModel.gender).distinct().filter(ProfileModel.tags.in_(selected_population_tags)).all()
    locations = db.session.query(ProfileModel.location).distinct().filter(ProfileModel.tags.in_(selected_population_tags)).all()
    ethnicities = db.session.query(ProfileModel.ethnicity).distinct().filter(ProfileModel.tags.in_(selected_population_tags)).all()
    occupations = db.session.query(ProfileModel.occupation).distinct().filter(ProfileModel.tags.in_(selected_population_tags)).all()
    education_levels = db.session.query(ProfileModel.education_level).distinct().filter(ProfileModel.tags.in_(selected_population_tags)).all()
    religions = db.session.query(ProfileModel.religion).distinct().filter(ProfileModel.tags.in_(selected_population_tags)).all()
    health_statuses = db.session.query(ProfileModel.health_status).distinct().filter(ProfileModel.tags.in_(selected_population_tags)).all()
    legal_statuses = db.session.query(ProfileModel.legal_status).distinct().filter(ProfileModel.tags.in_(selected_population_tags)).all()
    marital_statuses = db.session.query(ProfileModel.marital_status).distinct().filter(ProfileModel.tags.in_(selected_population_tags)).all()

    form.gender.choices = [('Any', 'Any')] + [(gender[0], gender[0]) for gender in genders]
    form.location.choices = [('Any', 'Any')] + [(location[0], location[0]) for location in locations]
    form.ethnicity.choices = [('Any', 'Any')] + [(ethnicity[0], ethnicity[0]) for ethnicity in ethnicities]
    form.occupation.choices = [('Any', 'Any')] + [(occupation[0], occupation[0]) for occupation in occupations]
    form.education_level.choices = [('Any', 'Any')] + [(education_level[0], education_level[0]) for education_level in education_levels]
    form.religion.choices = [('Any', 'Any')] + [(religion[0], religion[0]) for religion in religions]
    form.health_status.choices = [('Any', 'Any')] + [(health_status[0], health_status[0]) for health_status in health_statuses]
    form.legal_status.choices = [('Any', 'Any')] + [(legal_status[0], legal_status[0]) for legal_status in legal_statuses]
    form.marital_status.choices = [('Any', 'Any')] + [(marital_status[0], marital_status[0]) for marital_status in marital_statuses]

    # Add income range options to the form
    form.income_range.choices = [('Low', 'Low'), ('Medium', 'Medium'), ('High', 'High')]

    if form.validate_on_submit():
        new_filter = FilterModel(
            project_id=project.id,
            alias=form.alias.data,
            gender=form.gender.data if form.gender.data != 'Any' else None,
            age_min=form.age_min.data,
            age_max=form.age_max.data,
            location=form.location.data if form.location.data != 'Any' else None,
            ethnicity=form.ethnicity.data if form.ethnicity.data != 'Any' else None,
            occupation=form.occupation.data if form.occupation.data != 'Any' else None,
            education_level=form.education_level.data if form.education_level.data != 'Any' else None,
            religion=form.religion.data if form.religion.data != 'Any' else None,
            health_status=form.health_status.data if form.health_status.data != 'Any' else None,
            legal_status=form.legal_status.data if form.legal_status.data != 'Any' else None,
            marital_status=form.marital_status.data if form.marital_status.data != 'Any' else None,
            income_range=form.income_range.data,  # Add income range to new filter creation
        )
        db.session.add(new_filter)
        db.session.commit()
        flash('Segment created successfully!', 'success')
        return redirect(url_for('projects_bp.project_dashboard', project_id=project_id))
    else:
        print("Form validation failed:", form.errors)

    # If form validation fails, re-render the dashboard with errors
    projects = Project.query.filter_by(user_id=current_user.id, status='active').all()
    tags = db.session.query(ProjectPopulation.population_tag).filter_by(project_id=project.id).distinct().all()
    total_profiles = db.session.query(db.func.count()).filter(
        ProfileModel.tags.in_([tag[0] for tag in tags])
    ).scalar()
    profile_tags = db.session.query(ProfileModel.tags).distinct().all()

    return render_template(
        'project_dashboard.html', 
        project=project, 
        projects=projects, 
        tags=tags,
        total_profiles=total_profiles,
        profile_tags=profile_tags,
        form=form
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
    
    # set the reload flag to 0
    set_survey_reload_flag(survey_id, 0) 
    
    # Step 6: Provide feedback and redirect to the project dashboard
    flash(f'Survey "{project_survey.survey_alias}" has been queued...', 'success')
    return redirect(url_for('projects_bp.project_dashboard', project_id=project_id))


@projects_bp.route('/survey_progress/<int:project_survey_id>', methods=['GET'])
@login_required
def survey_progress(project_survey_id):
    progress = get_survey_progress(project_survey_id)
    rounded_progress = round(progress / 5) * 5
    
    # Check if the reload flag exists and get its value
    reload_flag = get_survey_reload_flag(project_survey_id)
    
    return jsonify({
        'progress': int(rounded_progress),
        'reload_flag': reload_flag
    })
    
    
@projects_bp.route('/set_survey_reload_flag/<int:project_survey_id>', methods=['POST'])
@login_required
def set_survey_reload_flag_route(project_survey_id):
    set_survey_reload_flag(project_survey_id, 1)
    return jsonify({'status': 'success'})