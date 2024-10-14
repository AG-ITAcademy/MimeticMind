from flask import Blueprint, render_template, request, jsonify, abort, redirect, url_for, g
from models import ProfileModel, Population, db
from forms import PopulationFilterForm
from sqlalchemy import func
from datetime import datetime, timedelta
from flask_login import login_required

population_explorer_bp = Blueprint('population_explorer_bp', __name__)

@population_explorer_bp.route('/population_explorer', methods=['GET', 'POST'])
@login_required
def population_explorer():
    form = PopulationFilterForm(request.form)
    population_tag = request.args.get('population')
    
    if not population_tag:
        first_population = Population.query.first()
        if first_population:
            return redirect(url_for('population_explorer_bp.population_explorer', population=first_population.tag))
        else:
            abort(404, description="No populations available")
    
    population = Population.query.filter_by(tag=population_tag).first_or_404()
    
    query = ProfileModel.query.filter(ProfileModel.tags.contains(population_tag))
    
    if request.method == 'POST':
        if form.validate():
            query = apply_filters_to_query(query, form)
        else:
            return jsonify({'error': 'Invalid form data'}), 400
    
    profiles = query.limit(100).all()
    age_groups = get_age_groups(query)
    gender_distribution = get_gender_distribution(query)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            "data": [profile_to_dict(profile) for profile in profiles],
            "age_groups": age_groups,
            "gender_distribution": gender_distribution
        })
    else:
        return render_template('population_explorer.html', 
                               population=population,
                               form=form, 
                               profiles=[profile_to_dict(profile) for profile in profiles],
                               age_groups=age_groups,
                               gender_distribution=gender_distribution)

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

def profile_to_dict(profile):
    return {
        'profile_name': profile.profile_name,
        'gender': profile.gender,
        'occupation': profile.occupation,
        'income_range': profile.income_range,
        'education_level': profile.education_level
    }

def get_age_groups(query):
    current_date = datetime.now()
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
        count = query.filter(ProfileModel.birth_date.between(min_date, max_date)).count()
        if count > 0:
            age_groups.append({"name": range_name, "value": count})
    return age_groups

def get_gender_distribution(query):
    gender_counts = query.with_entities(ProfileModel.gender, func.count(ProfileModel.id)).group_by(ProfileModel.gender).all()
    return [{"name": gender, "value": max(1, count)} for gender, count in gender_counts]

@population_explorer_bp.route('/save_segment', methods=['POST'])
@login_required
def save_segment():
    # Implement segment saving logic here
    pass