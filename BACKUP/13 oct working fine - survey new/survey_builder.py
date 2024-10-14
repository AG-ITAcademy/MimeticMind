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
    form.survey_id.data = survey_template.id  # Explicitly set the survey_id
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
    template_id = request.args.get('template_id')
    
    if template_id:
        template = SurveyTemplate.query.get_or_404(template_id)
        form = SurveyForm(obj=template)
        survey = SurveyTemplate(
            name=f"Copy of {template.name}",
            description=template.description,
            context_prompt=template.context_prompt,
            user_id=current_user.id
        )
        # Copy query templates
        for query in template.query_templates:
            new_query = QueryTemplate(
                name=query.name,
                query_text=query.query_text,
                schema=query.schema
            )
            survey.query_templates.append(new_query)
    else:
        survey = SurveyTemplate(name="New Survey", user_id=current_user.id)
    
    if form.validate_on_submit():
        form.populate_obj(survey)
        db.session.add(survey)
        db.session.commit()
        flash('Survey created successfully.', 'success')
        return redirect(url_for('survey_builder_bp.edit_survey', template_id=survey.id))

    # Extract schema options from schema_mapping
    schema_options = list(schema_mapping.keys()) if schema_mapping else []

    return render_template('survey_builder.html', form=form, survey=survey, schema_options=schema_options)
    
    
    
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
        return jsonify({'error': 'Survey ID is required for updating an existing survey.'}), 400
    
    # Update survey details
    survey.name = data.get('name')
    survey.description = data.get('description')
    survey.context_prompt = data.get('context_prompt')
    
    # Process queries
    existing_queries = {str(query.id): query for query in survey.query_templates}
    updated_queries = []
    
    for query_data in data.get('query_templates', []):
        query_id = str(query_data.get('id'))
        if query_id and query_id in existing_queries:
            # Update existing query
            query = existing_queries[query_id]
            query.name = query_data['name'] or query_data['query_text']  # Use query_text as fallback
            query.query_text = query_data['query_text']
            query.schema = query_data['schema']
            updated_queries.append(query)
        else:
            # Add new query
            new_query = QueryTemplate(
                name=query_data['name'] or query_data['query_text'],  # Use query_text as fallback
                query_text=query_data['query_text'],
                schema=query_data['schema']
            )
            updated_queries.append(new_query)
    
    # Update the survey's query templates
    survey.query_templates = updated_queries
    
    try:
        db.session.commit()
        return jsonify({'message': 'Survey saved successfully', 'survey_id': survey.id}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500