from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from models import db, Project, ProjectSurvey, QueryTemplate, SurveyTemplate
from forms import PopulationFilterForm
from answer_schema import get_analysis_methods
from models_view import ScaleResponse, OpenEndedResponse, MultipleChoiceResponse, YesNoResponse, RankingResponse
from sqlalchemy import text
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


# Route to fetch survey data based on question type
@survey_analysis_bp.route('/get_survey_data/<int:question_id>', methods=['GET'])
@login_required
def get_survey_data(question_id):
    question = QueryTemplate.query.get(question_id)
    
    if not question:
        return jsonify({'error': 'Question not found'}), 404

    # Fetch responses based on the schema type using raw SQL
    if question.schema == 'ScaleSchema':
        sql = text("SELECT * FROM vw_scale_responses WHERE query_template_id = :question_id")
    elif question.schema == 'OpenEndedSchema':
        sql = text("SELECT * FROM vw_open_ended_responses WHERE query_template_id = :question_id")
    elif question.schema == 'MultipleChoiceSchema':
        sql = text("SELECT * FROM vw_multiple_choice_responses WHERE query_template_id = :question_id")
    elif question.schema == 'YesNoSchema':
        sql = text("SELECT * FROM vw_yes_no_responses WHERE query_template_id = :question_id")
    elif question.schema == 'RankingSchema':
        sql = text("SELECT * FROM vw_ranking_responses WHERE query_template_id = :question_id")

    # Execute the SQL query
    result = db.session.execute(sql, {'question_id': question_id})

    # Format the result into the required structure
    response_data = []
    for row in result:
        data = {
            'gender': row.gender,
            'occupation': row.occupation,
            'income_range': row.income_range,
            'education_level': row.education_level,
            'item': getattr(row, 'item', None),  # This will be None for non-Ranking schemas
            'response': getattr(row, 'response', None) or getattr(row, 'choice', None) or getattr(row, 'rating', None) or getattr(row, 'rank', None)
        }
        response_data.append(data)

    return jsonify({'surveyData': response_data})
    
    
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