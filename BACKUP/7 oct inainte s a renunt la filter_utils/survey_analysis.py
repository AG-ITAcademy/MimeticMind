from flask import Blueprint, render_template, request, jsonify, abort, redirect, url_for
from models import ProfileModel, Population, db
from filter_utils import FilterForm, populate_filter_form_choices, get_filtered_profiles
from sqlalchemy import func
from datetime import datetime, timedelta, date
from flask_login import login_required
from collections import Counter

survey_analysis_bp = Blueprint('survey_analysis_bp', __name__)

@survey_analysis_bp.route('/survey_analysis/<int:project_survey_id>', methods=['GET', 'POST'])
@login_required
def survey_analysis(project_survey_id):
    project_survey_id = request.args.get('project_survey_id')
    
    form = FilterForm(request.form)
    populate_filter_form_choices(form)
    
    if request.method == 'POST' and form.validate():
        profiles = get_filtered_profiles(population_tag, form.data)
    else:
        profiles = ProfileModel.query.filter(ProfileModel.tags.contains(population_tag)).limit(100).all()
        
    profiles_data = [profile_to_dict(profile) for profile in profiles]
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            "data": profiles_data
        })
    
    return render_template('survey_analysis.html', 
                           population=population,
                           form=form, 
                           profiles=profiles_data,
                           age_groups=age_groups,
                           gender_distribution=gender_distribution)


def profile_to_dict(profile):
    return {
        'profile_name': profile.profile_name,
        'gender': profile.gender,
        'occupation': profile.occupation,
        'income_range': profile.income_range,
        'education_level': profile.education_level
    }
