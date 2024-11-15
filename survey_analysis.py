#survey_analysis.py
"""
Blueprint for survey analysis functionality.
Handles data visualization, filtering, and export of survey responses with various analysis methods.
"""

from flask import Blueprint, render_template, request, jsonify
from models import ProfileView, ProjectSurvey, SurveyTemplate, QueryTemplate, db, Population
from filter_utils import FilterForm, populate_filter_form_choices, get_filtered_profiles
from answer_schema import get_data_from_schema
from flask_login import login_required
from sqlalchemy import text
from analysis_utils import perform_sentiment_analysis, calculate_word_frequency
from flask import send_file
import csv
import io

survey_analysis_bp = Blueprint('survey_analysis_bp', __name__)

@survey_analysis_bp.route('/survey_analysis/<int:project_survey_id>', methods=['GET', 'POST'])
@login_required
def survey_analysis(project_survey_id):
    """  Display and filter survey analysis with charts and response data. Handles both initial page load and AJAX requests for filtered data. """
    print(f"survey_analysis function called for project_survey_id: {project_survey_id}")

    question_id = request.form.get('selected_question_id')
    project_survey = ProjectSurvey.query.get_or_404(project_survey_id)
    population_tag = request.args.get('population_tag')

    population = Population.query.filter_by(tag=population_tag).first()

    survey_template = SurveyTemplate.query.get(project_survey.survey_template_id)
    questions = survey_template.query_templates
    form = FilterForm(request.form)
    populate_filter_form_choices(form, population_tag)
    print('population_tag: '+str(population_tag))
    print(form.gender.choices)
   
    if request.method == 'POST' and form.validate():
        profiles = get_filtered_profiles(population_tag, form.data).all()
    else:
        profiles = ProfileView.query.filter(ProfileView.tags.contains(population_tag)).all()
        
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
    
    # Collect all unique analysis methods
    all_analysis_methods = set()
    for question in questions:
        question_data = get_data_from_schema(question.schema)
        all_analysis_methods.update(method['name'] for method in question_data.get('methods', []))

    # Convert the set to a sorted list
    all_analysis_methods = sorted(list(all_analysis_methods))
    
    return render_template('survey_analysis.html', 
                           form=form, 
                           population=population.name,
                           project_survey=project_survey,
                           questions=questions,
                           respondents= project_survey.respondents,
                           description=survey_template.description,
                           data=response_data,
                           question_data=question_data,
                           all_analysis_methods=all_analysis_methods)

@survey_analysis_bp.route('/download_raw_data/<int:project_survey_id>', methods=['GET'])
@login_required
def download_raw_data(project_survey_id):
    """Export survey responses and demographic data as CSV."""
    
    project_survey = ProjectSurvey.query.get_or_404(project_survey_id)
    survey_template = SurveyTemplate.query.get(project_survey.survey_template_id)
    questions = survey_template.query_templates
    
    # Create a StringIO object to store CSV data
    si = io.StringIO()
    cw = csv.writer(si)

    # Write header
    header = ['Profile ID', 'Question', 'Response']
    cw.writerow(header)

    # Fetch and write data
    for question in questions:
        result = db.session.execute(text("""
            SELECT p.id, p.birth_date, p.gender, p.education_level, p.occupation, p.income_range, 
            p.location, p.health_status, p.ethnicity, p.legal_status, p.religion, p.marital_status,
            p.hobbies, qt.query_text, i.answer_text
            FROM interactions i
            JOIN query_templates qt ON i.template_id = qt.id
            JOIN profiles p on p.id = i.profile_id
            WHERE i.project_survey_id = :project_survey_id AND i.template_id = :question_id
        """), {'project_survey_id': project_survey_id, 'question_id': question.id})

        for row in result:
            cw.writerow([
                row.id, row.birth_date, row.gender, row.education_level, row.occupation,
                row.income_range, row.location, row.health_status, row.ethnicity, row.legal_status,
                row.religion, row.marital_status, row.hobbies, row.query_text, row.answer_text
            ])

    # Prepare the CSV file for download
    output = io.BytesIO()
    output.write(si.getvalue().encode('utf-8'))
    output.seek(0)
    
    return send_file(
        output,
        as_attachment=True,
        download_name=f'survey_data_{project_survey_id}.csv',
        mimetype='text/csv'
    )



def build_options(question_data):
    """ Build visualization options for different analysis methods. """
    
    for method in question_data['methods']:
        chart_data = method['chart_data']
        print(chart_data)
        if method['name'] == 'Frequency Distribution':
            responses = [item['response'] for item in chart_data]
            categories = [
                'Total',
                'Gender: Male', 'Gender: Female', 
                'Marital: Single', 'Marital: Married', 'Marital: Divorced', 'Marital: Widowed', 'Marital: Separated',
                'Health: Excellent', 'Health: Very Good', 'Health: Good', 'Health: Fair', 'Health: Poor',
                'Income: Low', 'Income: Medium', 'Income: High',
                'Education: < High School', 'Education: HS Graduate', 'Education: Associate', 'Education: Bachelor', 'Education: Master/PhD'
            ]
            series = [{
                'name': category,
                'type': 'bar',
                'stack': 'total',
                'data': [item[key] for item in chart_data],
                'label': {
                    'show': True,
                    'position': 'inside',
                    'formatter': '{c}',
                    'fontSize': 12,
                    'fontWeight': 'bold',
                    'color': '#fff'
                },
                'emphasis': {
                    'label': {
                        'show': True,
                        'fontSize': 14,
                        'fontWeight': 'bold',
                        'color': '#fff'
                    }
                }
            } for category, key in zip(categories, [
                'total',
                'male', 'female', 
                'single', 'married', 'divorced', 'widowed', 'separated',
                'health_excellent', 'health_very_good', 'health_good', 'health_fair', 'health_poor',
                'income_low', 'income_medium', 'income_high',
                'edu_less_than_hs', 'edu_hs_graduate', 'edu_associate', 'edu_bachelor', 'edu_master_phd'
            ])]
            method['chart_option'] = {
                "tooltip": {
                    "trigger": "axis",
                    "axisPointer": {"type": "shadow"}
                },
                "legend": {
                    "data": categories,
                    "type": 'scroll',
                    "orient": 'horizontal',
                    "top": 0,
                    "left": 'center',
                    "width": '80%',
                    "pageButtonPosition": 'end',
                    "textStyle": {
                        "color": '#B2BEB5'
                    },
                    "height": 25,  
                    "padding": [5, 10]
                },
                "grid": {
                    "left": '3%',
                    "right": '10%',  
                    "bottom": '3%',
                    "top": '10%',  
                    "containLabel": True
                },
                "toolbox": {
                    "show": True,
                    "orient": 'vertical',
                    "left": 'right',
                    "top": 'center',
                    "feature": {
                        "dataView": { "show": True, "readOnly": True },
                        "magicType": { "show": True, "type": ['bar', 'stack'] },
                        "restore": { "show": True },
                        "saveAsImage": { "show": True }
                    }
                },
                "xAxis": {
                    "type": "value"
                },
                "yAxis": {
                    "type": "category",
                    "data": responses,
                    "inverse": True
                },
                "series": series
            }
            
        elif method['name'] == 'Descriptive Statistics':
            if chart_data:
                stats = chart_data[0]
                method['chart_option'] = {
                    "tooltip": {"trigger": "axis"},
                    "xAxis": {"type": "category", "data": ['Min', 'Max', 'Average']},
                    "yAxis": {"type": "value"},
                    "series": [{
                        "data": [stats['min'], stats['max'], stats['avg']],
                        "type": 'bar'
                    }]
                }
        
        elif method['name'] == 'Sentiment Analysis':
            responses = [item['response'] for item in chart_data]
            sentiment_data = perform_sentiment_analysis(responses)
            method['chart_option'] = {
                "tooltip": {
                    "trigger": "item",
                    "formatter": "{a} <br/>{b}: {c} ({d}%)"
                },
                "legend": {
                    "data": [item['sentiment'] for item in sentiment_data],
                    "type": 'scroll',
                    "orient": 'horizontal',
                    "top": 0,
                    "left": 'center',
                    "width": '80%',
                    "pageButtonPosition": 'end',
                    "textStyle": {
                        "color": '#B2BEB5'
                    },
                    "height": 25,  
                    "padding": [5, 10]
                },
                "grid": {
                    "left": '3%',
                    "right": '10%',  
                    "bottom": '3%',
                    "top": '10%',  
                    "containLabel": True
                },
                "toolbox": {
                    "show": True,
                    "orient": 'vertical',
                    "left": 'right',
                    "top": 'center',
                    "feature": {
                        "dataView": { "show": True, "readOnly": True },
                        "restore": { "show": True },
                        "saveAsImage": { "show": True }
                    }
                },
                "series": [{
                    "name": 'Sentiment',
                    "type": 'pie',
                    "radius": ['40%', '70%'],
                    "center": ['50%', '60%'],
                    "avoidLabelOverlap": False,
                    "itemStyle": {
                        "borderRadius": 10,
                        "borderColor": '#fff',
                        "borderWidth": 0
                    },
                    "label": {
                        "show": True,
                        "formatter": '{b}: {c} ({d}%)',
                        "textStyle": {"color": '#B2BEB5'},
                        "textBorderColor": 'transparent',  
                        "textShadowColor": 'transparent'  
                    },
                    "emphasis": {
                        "label": {
                            "show": True,
                            "fontSize": '14',
                            "fontWeight": 'bold'
                        }
                    },
                    "labelLine": {
                        "show": True
                    },
                    "data": [{"value": item['count'], "name": item['sentiment']} for item in sentiment_data]
                }]
            }
        
        elif method['name'] == 'Word Frequency':
            responses = [item['response'] for item in chart_data]
            word_freq_data = calculate_word_frequency(responses)
            method['chart_option'] = {
                "tooltip": {},
                "series": [{
                    "type": 'wordCloud',
                    "sizeRange": [20, 80],
                    "rotationRange": [0, 0],
                    "shape": 'circle',
                    "width": '130%',
                    "height": '130%',
                    "textStyle": {
                        "color": '#B2BEB5'  # Apply color universally to the word cloud
                    },
                    "data": [{"name": item['word'], "value": item['frequency']} for item in word_freq_data]
                }]
            }
        
        elif method['name'] == 'Cluster Analysis':
            data = [[item['age'], item['choice']] for item in chart_data]
            unique_choices = list(set(item['choice'] for item in chart_data))
            
            method['chart_option'] = {
                "tooltip": {
                    "trigger": 'item'
                },
                "legend": {
                    "data": unique_choices,
                    "type": 'scroll',
                    "orient": 'horizontal',
                    "top": 30,
                    "left": 'center',
                    "width": '80%',
                    "pageButtonPosition": 'end',
                    "textStyle": {
                        "color": '#B2BEB5'
                    }
                },
                "grid": {
                    "left": '3%',
                    "right": '10%',
                    "bottom": '3%',
                    "top": '15%',
                    "containLabel": True
                },
                "toolbox": {
                    "show": True,
                    "orient": 'vertical',
                    "left": 'right',
                    "top": 'center',
                    "feature": {
                        "dataZoom": {},
                        "dataView": { "show": True, "readOnly": True },
                        "restore": { "show": True },
                        "saveAsImage": { "show": True }
                    }
                },
                "xAxis": {
                    "type": 'value',
                    "name": 'Age',
                    "nameLocation": 'middle',
                    "nameGap": 30,
                    "nameTextStyle": {
                        "color": '#B2BEB5'
                    },
                    "axisLabel": {
                        "color": '#B2BEB5'
                    }
                },
                "yAxis": {
                    "type": 'category',
                    "name": 'Choice',
                    "nameLocation": 'middle',
                    "nameGap": 40,
                    "nameTextStyle": {
                        "color": '#B2BEB5'
                    },
                    "axisLabel": {
                        "color": '#B2BEB5'
                    },
                    "data": unique_choices
                },
                "series": [{
                    "name": 'Clusters',
                    "type": 'scatter',
                    "symbolSize": 10,
                    "data": data,
                    "itemStyle": {
                        "opacity": 0.8
                    },
                    "emphasis": {
                        "itemStyle": {
                            "shadowBlur": 10,
                            "shadowOffsetX": 0,
                            "shadowColor": 'rgba(0, 0, 0, 0.5)'
                        }
                    }
                }]
            }
        
        elif method['name'] == 'Mean Rank Calculation':
            items = [item['item'] for item in chart_data]
            categories = [
                'Total', 'Gender: Male', 'Gender: Female', 
                'Marital: Single', 'Marital: Married', 'Marital: Divorced', 'Marital: Widowed', 'Marital: Separated',
                'Health: Excellent', 'Health: Very Good', 'Health: Good', 'Health: Fair', 'Health: Poor',
                'Income: Low', 'Income: Medium', 'Income: High',
                'Education: < High School', 'Education: HS Graduate', 'Education: Associate', 'Education: Bachelor', 'Education: Master/PhD'
            ]
            series = [{
                'name': category,
                'type': 'bar',
                'data': [item[key] for item in chart_data],
                "itemStyle": {
                    "borderRadius": [5, 5, 0, 0]
                },
                "emphasis": {
                    "itemStyle": {
                        "brightness": 0.2
                    }
                },
                "label": {
                    "show": True,
                    "position": 'top',
                    "color": '#B2BEB5',
                }
            } for category, key in zip(categories, [
                'total', 'male', 'female', 
                'single', 'married', 'divorced', 'widowed', 'separated',
                'health_excellent', 'health_very_good', 'health_good', 'health_fair', 'health_poor',
                'income_low', 'income_medium', 'income_high',
                'edu_less_than_hs', 'edu_hs_graduate', 'edu_associate', 'edu_bachelor', 'edu_master_phd'
            ])]
            
            method['chart_option'] = {
                "title": {
                    "text": "Mean Rank Calculation",
                    "left": 'center',
                    "top": 0,
                    "textStyle": {
                        "color": '#B2BEB5'
                    }
                },
                "tooltip": {
                    "trigger": 'axis',
                    "axisPointer": {
                        "type": 'shadow'
                    },
                },
                "legend": {
                    "data": categories,
                    "type": 'scroll',
                    "orient": 'horizontal',
                    "top": 30,
                    "left": 'center',
                    "width": '80%',
                    "pageButtonPosition": 'end',
                    "textStyle": {
                        "color": '#B2BEB5'
                    }
                },
                "grid": {
                    "left": '3%',
                    "right": '10%',
                    "bottom": '3%',
                    "top": '15%',
                    "containLabel": True
                },
                "toolbox": {
                    "show": True,
                    "orient": 'vertical',
                    "left": 'right',
                    "top": 'center',
                    "feature": {
                        "dataZoom": {},
                        "dataView": { "show": True, "readOnly": True },
                        "magicType": { "type": ['line', 'bar'] },
                        "restore": { "show": True },
                        "saveAsImage": { "show": True }
                    }
                },
                "xAxis": {
                    "type": 'category',
                    "data": items,
                    "axisLabel": {
                        "color": '#B2BEB5',
                        "rotate": 45,
                        "interval": 0
                    },
                    "axisLine": {
                        "lineStyle": {
                            "color": '#B2BEB5'
                        }
                    }
                },
                "yAxis": {
                    "type": 'value',
                    "name": 'Mean Rank',
                    "nameLocation": 'middle',
                    "nameGap": 40,
                    "nameTextStyle": {
                        "color": '#B2BEB5'
                    },
                    "axisLabel": {
                        "color": '#B2BEB5'
                    },
                    "axisLine": {
                        "lineStyle": {
                            "color": '#B2BEB5'
                        }
                    }
                },
                "series": series
            }
            
            
    return question_data