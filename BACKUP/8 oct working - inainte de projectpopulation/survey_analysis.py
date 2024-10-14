from flask import Blueprint, render_template, request, jsonify
from models import ProfileModel, ProjectSurvey, SurveyTemplate, QueryTemplate, db
from filter_utils import FilterForm, populate_filter_form_choices, get_filtered_profiles
from answer_schema import get_data_from_schema
from flask_login import login_required
from sqlalchemy import text

survey_analysis_bp = Blueprint('survey_analysis_bp', __name__)

@survey_analysis_bp.route('/survey_analysis/<int:project_survey_id>', methods=['GET', 'POST'])
@login_required
def survey_analysis(project_survey_id):
    print(f"survey_analysis function called for project_survey_id: {project_survey_id}")

    question_id = request.form.get('selected_question_id')
    project_survey = ProjectSurvey.query.get_or_404(project_survey_id)
    population_tag = request.args.get('population_tag')
    survey_template = SurveyTemplate.query.get(project_survey.survey_template_id)
    questions = survey_template.query_templates
    form = FilterForm(request.form)
    populate_filter_form_choices(form, population_tag)
   
    if request.method == 'POST' and form.validate():
        profiles = get_filtered_profiles(population_tag, form.data).all()
    else:
        profiles = ProfileModel.query.filter(ProfileModel.tags.contains(population_tag)).all()
        
    profile_ids = [profile.id for profile in profiles]
    question = QueryTemplate.query.get(question_id)
    print("query template ID:"+str(question_id))

    question_data={}
    response_data = []
    if question:
        # Get all data corresponding to question.schema
        question_data = get_data_from_schema(question.schema)
        result = db.session.execute(text(question_data['raw_sql']), {'question_id': question_id, 'profile_ids': tuple(profile_ids or [0]), 'project_survey_id': project_survey_id})
        
        # prepare table data
        for row in result:
            raw_data = {
                'gender': row.gender,
                'occupation': row.occupation,
                'income_range': row.income_range,
                'education_level': row.education_level,
                'item': getattr(row, 'item', None),  # This will be None for non-Ranking schemas
                'response': getattr(row, 'response', None) or getattr(row, 'choice', None) or getattr(row, 'rating', None) or getattr(row, 'rank', None)
            }
            response_data.append(raw_data)
            
        # prepare question specific data (for charts)
        for method in question_data['methods']:
            chart_data = []
            result = db.session.execute(text(method['chart_sql']), {'question_id': question_id, 'profile_ids': tuple(profile_ids or [0]), 'project_survey_id': project_survey_id})
            for row in result:
                raw_data = {}
                for key, value in zip(result.keys(), row):
                    raw_data[key] = value
                chart_data.append(raw_data)
            method['chart_data'] = chart_data
        question_data = build_options(question_data) # pregateste option pentru chart in frontend

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            "data": response_data,  # Table data
            "question_data": question_data  # Analysis method data, including chart data
        })
    
    return render_template('survey_analysis.html', 
                           form=form, 
                           population=population_tag,
                           project_survey=project_survey,
                           questions=questions,
                           data=response_data,
                           question_data=question_data)


def build_options(question_data):
    for method in question_data['methods']:
        chart_data = method['chart_data']
        print(chart_data)
        if method['name'] == 'Frequency Distribution':
            labels = [str(item['response']) for item in chart_data]
            values = [item['frequency'] for item in chart_data]
            method['chart_option'] = {
                "title": {"text": method['name']},
                "tooltip": {},
                "xAxis": {"type": "category", "data": labels},
                "yAxis": {"type": "value"},
                "series": [{"data": values, "type": 'bar'}]
            }
        
        elif method['name'] == 'Descriptive Statistics':
            if chart_data:
                stats = chart_data[0]
                method['chart_option'] = {
                    "title": {"text": method['name']},
                    "tooltip": {"trigger": "axis"},
                    "xAxis": {"type": "category", "data": ['Min', 'Max', 'Average']},
                    "yAxis": {"type": "value"},
                    "series": [{
                        "data": [stats['min'], stats['max'], stats['avg']],
                        "type": 'bar'
                    }]
                }
        
        elif method['name'] == 'Sentiment Analysis':
            sentiments = {'Positive': 0, 'Neutral': 0, 'Negative': 0}
            for item in chart_data:
                sentiments[item['sentiment']] = item['count']
            method['chart_option'] = {
                "title": {"text": method['name']},
                "tooltip": {"trigger": "item"},
                "legend": {"orient": "vertical", "left": "left"},
                "series": [{
                    "type": 'pie',
                    "radius": "50%",
                    "data": [{"value": v, "name": k} for k, v in sentiments.items()],
                    "emphasis": {
                        "itemStyle": {
                            "shadowBlur": 10,
                            "shadowOffsetX": 0,
                            "shadowColor": "rgba(0, 0, 0, 0.5)"
                        }
                    }
                }]
            }
        
        elif method['name'] == 'Word Frequency':
            words = [item['word'] for item in chart_data]
            frequencies = [item['frequency'] for item in chart_data]
            method['chart_option'] = {
                "title": {"text": method['name']},
                "tooltip": {},
                "xAxis": {"type": "category", "data": words},
                "yAxis": {"type": "value"},
                "series": [{"data": frequencies, "type": 'bar'}]
            }
        
        elif method['name'] == 'Cluster Analysis':
            data = [[item['age'], item['choice']] for item in chart_data]
            method['chart_option'] = {
                "title": {"text": method['name']},
                "xAxis": {},
                "yAxis": {},
                "series": [{
                    "symbolSize": 20,
                    "data": data,
                    "type": 'scatter'
                }]
            }
        
        elif method['name'] == 'Mean Rank Calculation':
            items = [item['item'] for item in chart_data]
            mean_ranks = [item['mean_rank'] for item in chart_data]
            method['chart_option'] = {
                "title": {"text": method['name']},
                "tooltip": {},
                "xAxis": {"type": "category", "data": items},
                "yAxis": {"type": "value"},
                "series": [{"data": mean_ranks, "type": 'bar'}]
            }
    
    return question_data