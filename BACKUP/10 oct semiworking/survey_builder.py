from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import Project, db, Population, SurveyTemplate, ProjectSurvey, QueryTemplate
from sqlalchemy.orm import joinedload
from flask_wtf.csrf import CSRFProtect
from flask import jsonify
from answer_schema import schema_mapping
from forms import SurveyForm

survey_builder_bp = Blueprint('survey_builder_bp', __name__)
csrf = CSRFProtect()

@survey_builder_bp.route('/survey/create')
@login_required
def create_survey():
    projects = Project.query.filter_by(user_id=current_user.id, status='active').all()
    populations = Population.query.all()
    templates = SurveyTemplate.query.all()  # This will include both default and user-defined templates
    return render_template('survey_create.html', projects=projects, populations=populations, templates=templates)

@survey_builder_bp.route('/surveys')
@login_required
def list_surveys():
    survey_templates = SurveyTemplate.query.filter_by(user_id=current_user.id).options(
        joinedload(SurveyTemplate.project_surveys).joinedload(ProjectSurvey.project)
    ).all()
    return render_template('survey_edit.html', survey_templates=survey_templates)

@survey_builder_bp.route('/survey/edit/<int:template_id>')
@login_required
def edit_survey(template_id):
    survey_template = SurveyTemplate.query.get_or_404(template_id)
    if survey_template.user_id and survey_template.user_id != current_user.id:
        flash('You do not have permission to edit this survey template.', 'danger')
        return redirect(url_for('survey_builder_bp.list_surveys'))
    form = SurveyForm(obj=survey_template)
    schema_options = list(schema_mapping.keys()) if schema_mapping else []
    return render_template('survey_builder.html', form=form, survey=survey_template, schema_options=schema_options)

@survey_builder_bp.route('/survey/delete/<int:template_id>', methods=['POST'])
@login_required
def delete_survey(template_id):
    survey_template = SurveyTemplate.query.get_or_404(template_id)
    if not survey_template.user_id or survey_template.user_id != current_user.id:
        flash('You do not have permission to delete this survey template.', 'danger')
        return redirect(url_for('survey_builder_bp.list_surveys'))
    
    db.session.delete(survey_template)
    db.session.commit()
    flash('Survey template has been deleted.', 'success')
    return redirect(url_for('survey_builder_bp.list_surveys'))


@survey_builder_bp.route('/survey/build', methods=['GET', 'POST'])
@login_required
def build_survey():
    form = SurveyForm()

    if form.validate_on_submit():
        if form.survey_id.data:
            survey = SurveyTemplate.query.get_or_404(form.survey_id.data)
            if survey.user_id != current_user.id:
                flash('You do not have permission to edit this survey.', 'danger')
                return redirect(url_for('survey_builder_bp.list_surveys'))
        else:
            survey = SurveyTemplate(user_id=current_user.id)
            db.session.add(survey)

        form.populate_obj(survey)
        db.session.commit()
        flash('Survey saved successfully.', 'success')
        return redirect(url_for('survey_builder_bp.list_surveys'))

    template_id = request.args.get('template_id')
    if template_id:
        template = SurveyTemplate.query.get_or_404(template_id)
        form = SurveyForm(obj=template)
        form.survey_id.data = None  # Ensure we create a new survey

    # Extract schema options from schema_mapping
    schema_options = list(schema_mapping.keys()) if schema_mapping else []  # Default to an empty list if it's undefined
    print("Schema mapping keys:", list(schema_mapping.keys())) 

    return render_template('survey_builder.html', form=form, schema_options=schema_options)
    
@survey_builder_bp.route('/survey/save', methods=['POST'])
@login_required
def save_survey():
    data = request.json
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    survey_id = data.get('survey_id')
    
    if survey_id:
        survey = SurveyTemplate.query.get_or_404(survey_id)
        if survey.user_id != current_user.id:
            return jsonify({'error': 'You do not have permission to edit this survey.'}), 403
    else:
        survey = SurveyTemplate(user_id=current_user.id)
        db.session.add(survey)
    
    # Update survey details
    survey.name = data.get('name')
    survey.description = data.get('description')
    survey.context_prompt = data.get('context_prompt')
    
    # Process queries
    existing_query_ids = set(query.id for query in survey.query_templates)
    received_query_ids = set()
    
    for query_data in data.get('query_templates', []):
        query_id = query_data.get('id')
        if query_id:
            query = next((q for q in survey.query_templates if q.id == query_id), None)
            if query:
                query.query_text = query_data['query_text']
                query.schema = query_data['schema']
                received_query_ids.add(query_id)
            else:
                return jsonify({'error': f'Query with id {query_id} not found'}), 400
        else:
            new_query = QueryTemplate(
                query_text=query_data['query_text'],
                schema=query_data['schema'],
                survey_template=survey
            )
            db.session.add(new_query)
    
    # Remove queries that were deleted on the frontend
    for query in survey.query_templates:
        if query.id not in received_query_ids:
            db.session.delete(query)
    
    try:
        db.session.commit()
        return jsonify({'message': 'Survey saved successfully', 'survey_id': survey.id}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500