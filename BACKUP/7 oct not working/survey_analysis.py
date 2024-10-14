from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from models import db, Project, ProjectSurvey, QueryTemplate, SurveyTemplate, ProfileModel
from forms import PopulationFilterForm, FilterForm
from answer_schema import get_analysis_methods
from models_view import ScaleResponse, OpenEndedResponse, MultipleChoiceResponse, YesNoResponse, RankingResponse
from sqlalchemy import text,  and_
from collections import Counter  

survey_analysis_bp = Blueprint('survey_analysis_bp', __name__)

@survey_analysis_bp.route('/survey_analysis/<int:project_survey_id>', methods=['GET', 'POST'])
@login_required
def survey_analysis(project_survey_id):
    project_survey = ProjectSurvey.query.get(project_survey_id)
    survey_template = SurveyTemplate.query.get(project_survey.survey_template_id)
    questions = survey_template.query_templates
    
    form = PopulationFilterForm(request.form)
    
    selected_question = questions[0] if questions else None
    
    if request.method == 'POST':
        selected_question_id = request.form.get('question_id')
        selected_question = QueryTemplate.query.get(selected_question_id)
    
    analysis_methods = get_analysis_methods(selected_question.schema) if selected_question else []
    
    return render_template('survey_analysis.html',
                           project_survey=project_survey,
                           questions=questions,
                           selected_question=selected_question,
                           form=form,
                           analysis_methods=analysis_methods)


@survey_analysis_bp.route('/get_survey_data/<int:question_id>', methods=['GET'])
@login_required
def get_survey_data(question_id):
    question = QueryTemplate.query.get(question_id)
    
    if not question:
        return jsonify({'error': 'Question not found'}), 404

    form = FilterForm(request.args)
    
    # Get the appropriate response model
    response_model = {
        'ScaleSchema': ScaleResponse,
        'OpenEndedSchema': OpenEndedResponse,
        'MultipleChoiceSchema': MultipleChoiceResponse,
        'YesNoSchema': YesNoResponse,
        'RankingSchema': RankingResponse
    }.get(question.schema)

    if not response_model:
        return jsonify({'error': 'Invalid schema type'}), 400

    # Create the base query
    base_query = db.session.query(ProfileModel, response_model).select_from(ProfileModel).join(
        response_model,
        and_(
            response_model.profile_id == ProfileModel.id,
            response_model.query_template_id == question_id
        )
    )

    # Apply filters to the query
    filtered_query = apply_filters_to_query(base_query, form.data)

    # Execute the query
    results = filtered_query.all()

    # Format the result into the required structure
    response_data = []
    for profile, response in results:
        data = {
            'gender': profile.gender,
            'occupation': profile.occupation,
            'income_range': profile.income_range,
            'education_level': profile.education_level,
            'item': getattr(response, 'item', None),
            'response': getattr(response, 'response', None) or 
                        getattr(response, 'choice', None) or 
                        getattr(response, 'rating', None) or 
                        getattr(response, 'rank', None) or 
                        getattr(response, 'answer', None)
        }
        response_data.append(data)

    return jsonify({'surveyData': response_data})
    
    
def apply_filters_to_query(query, form):
    filters = [
        (form.gender.data, lambda x: ProfileModel.gender == x),
        (form.age_min.data, lambda x: ProfileModel.birth_date <= (datetime.now() - timedelta(days=365*int(x)))),
        (form.age_max.data, lambda x: ProfileModel.birth_date >= (datetime.now() - timedelta(days=365*int(x)))),
        (form.location.data, lambda x: ProfileModel.location.ilike(f'%{x}%')),
        (form.ethnicity.data, lambda x: ProfileModel.ethnicity.ilike(f'%{x}%')),
        (form.occupation.data, lambda x: ProfileModel.occupation.ilike(f'%{x}%')),
        (form.education_level.data, lambda x: ProfileModel.education_level.ilike(f'%{x}%')),
        (form.religion.data, lambda x: ProfileModel.religion.ilike(f'%{x}%')),
        (form.health_status.data, lambda x: ProfileModel.health_status.ilike(f'%{x}%')),
        (form.legal_status.data, lambda x: ProfileModel.legal_status.ilike(f'%{x}%')),
        (form.marital_status.data, lambda x: ProfileModel.marital_status.ilike(f'%{x}%')),
        (form.income_range.data, lambda x: ProfileModel.income_range == x),
    ]

    for value, filter_func in filters:
        if value:
            query = query.filter(filter_func(value))

    return query
    
@survey_analysis_bp.route('/get_chart_data/<int:question_id>', methods=['GET'])
@login_required
def get_chart_data(question_id):
    question = QueryTemplate.query.get(question_id)
    
    if not question:
        return jsonify({'error': 'Question not found'}), 404

    # Fetch responses based on the schema type using raw SQL
    if question.schema == 'ScaleSchema':
        sql = text("SELECT rating AS response FROM vw_scale_responses WHERE query_template_id = :question_id ORDER BY rating")
    elif question.schema == 'OpenEndedSchema':
        sql = text("SELECT response FROM vw_open_ended_responses WHERE query_template_id = :question_id ORDER BY response")
    elif question.schema == 'MultipleChoiceSchema':
        sql = text("SELECT choice AS response FROM vw_multiple_choice_responses WHERE query_template_id = :question_id")
    elif question.schema == 'YesNoSchema':
        sql = text("SELECT answer AS response FROM vw_yes_no_responses WHERE query_template_id = :question_id")
    elif question.schema == 'RankingSchema':
        sql = text("SELECT item, ROUND(AVG(rank), 1) AS response FROM vw_ranking_responses WHERE query_template_id = :question_id GROUP BY item ORDER by item")
    
    # Execute the SQL query
    result = db.session.execute(sql, {'question_id': question_id})

    # Process the result based on the schema
    if question.schema == 'RankingSchema':
        chart_data = [{'item': row.item, 'response': row.response} for row in result]
    else:
        responses = [row.response for row in result]
        response_counts = Counter(responses)
        chart_data = [{'item': item, 'response': count} for item, count in response_counts.items()]

    # Get analysis methods
    analysis_methods = get_analysis_methods(question.schema)

    return jsonify({
        'chartData': chart_data,
        'analysisMethods': analysis_methods,
        'schema': question.schema
    })