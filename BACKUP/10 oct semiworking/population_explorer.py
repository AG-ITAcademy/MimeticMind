from flask import Blueprint, render_template, request, jsonify, abort, redirect, url_for
from models import ProfileModel, Population, db
from filter_utils import FilterForm, populate_filter_form_choices, get_filtered_profiles
from sqlalchemy import func
from datetime import datetime, timedelta, date
from flask_login import login_required
from collections import Counter

population_explorer_bp = Blueprint('population_explorer_bp', __name__)

@population_explorer_bp.route('/population_explorer', methods=['GET', 'POST'])
@login_required
def population_explorer():
    population_tag = request.args.get('population')
    
    if not population_tag:
        first_population = Population.query.first()
        if first_population:
            return redirect(url_for('population_explorer_bp.population_explorer', population=first_population.tag))
        abort(404, description="No populations available")
    
    population = Population.query.filter_by(tag=population_tag).first_or_404()
    
    form = FilterForm(request.form)
    populate_filter_form_choices(form, population_tag)
    
    if request.method == 'POST' and form.validate():
        profiles = get_filtered_profiles(population_tag, form.data)
    else:
        profiles = ProfileModel.query.filter(ProfileModel.tags.contains(population_tag)).limit(100).all()
    
    age_groups = get_age_groups(profiles)
    gender_distribution = get_gender_distribution(profiles)
    
    profiles_data = [profile_to_dict(profile) for profile in profiles]
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            "data": profiles_data,
            "age_groups": age_groups,
            "gender_distribution": gender_distribution
        })
    
    return render_template('population_explorer.html', 
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

def get_age_groups(profiles):
    current_date = date.today()
    age_ranges = [
        ("<10", 0, 10),
        ("10-19", 10, 20),
        ("20-29", 20, 30),
        ("30-39", 30, 40),
        ("40-49", 40, 50),
        ("50-59", 50, 60),
        ("60-69", 60, 70),
        ("70-79", 70, 80),
        ("80+", 80, 200)
    ]
    age_groups = []
    for range_name, min_age, max_age in age_ranges:
        min_date = current_date - timedelta(days=365 * max_age)
        max_date = current_date - timedelta(days=365 * min_age)
        count = sum(1 for profile in profiles if min_date <= profile.birth_date <= max_date)
        if count > 0:
            age_groups.append({"name": range_name, "value": count})
    return age_groups

def get_gender_distribution(profiles):
    gender_counts = Counter(profile.gender for profile in profiles)
    return [{"name": gender, "value": max(1, count)} for gender, count in gender_counts.items()]

@population_explorer_bp.route('/save_segment', methods=['POST'])
@login_required
def save_segment():
    # Implement segment saving logic here
    pass