from flask import Blueprint, render_template, request, jsonify, abort, redirect, url_for
from models import Population, ProfileView
from filter_utils import FilterForm, populate_filter_form_choices, get_filtered_profiles
from datetime import timedelta, date
from flask_login import login_required
import logging
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
        profiles = ProfileView.query.filter(ProfileView.tags.contains(population_tag)).all()
    age_groups = get_age_groups(profiles)
    gender_distribution = get_gender_distribution(profiles)
    education_income_data = get_education_income(profiles)
    
    marital_status = get_marital_status(profiles)
    hobbies = get_hobbies(profiles)
    
    profiles_data = [profile_to_dict(profile) for profile in profiles]
    
    chart_data = {
        "data": profiles_data,
        "age_groups": age_groups,
        "gender_distribution": gender_distribution,
        "education_income": education_income_data['heatmap_data'],
        "education_levels": education_income_data['education_levels'],
        "income_levels": education_income_data['income_levels'],
        "marital_status": marital_status,
        "hobbies": hobbies
    }
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        logging.info("Responding to AJAX request")
        return jsonify(chart_data)
    
    logging.info("Rendering template")
    return render_template('population_explorer.html', 
                           population=population,
                           form=form, 
                           profiles=profiles_data,
                           age_groups=age_groups,
                           gender_distribution=gender_distribution,
                           education_income=education_income_data['heatmap_data'],
                           education_levels=education_income_data['education_levels'],
                           income_levels=education_income_data['income_levels'],
                           marital_status=marital_status,
                           hobbies=hobbies)

def profile_to_dict(profile):
    return {
        'profile_name': profile.profile_name,
        'gender': profile.gender,
        'occupation': profile.occupation,
        'income_range': profile.income_range,
        'education_level': profile.education_level,
        'hobbies': profile.hobbies.split(',') if profile.hobbies else []
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


def get_education_income(profiles):
    education_levels = sorted(set(profile.education_level for profile in profiles if profile.education_level))
    income_levels = sorted(set(profile.income_range for profile in profiles if profile.income_range))
    data = [[0 for _ in range(len(education_levels))] for _ in range(len(income_levels))]
    
    total_counted = 0
    for profile in profiles:
        if profile.education_level in education_levels and profile.income_range in income_levels:
            e_index = education_levels.index(profile.education_level)
            i_index = income_levels.index(profile.income_range)
            data[i_index][e_index] += 1
            total_counted += 1
    heatmap_data = [
        [j, i, data[i][j]]
        for i in range(len(income_levels))
        for j in range(len(education_levels))
    ]
    return {
        "heatmap_data": heatmap_data,
        "education_levels": education_levels,
        "income_levels": income_levels
    }


def get_marital_status(profiles):
    marital_status_counts = Counter(profile.marital_status for profile in profiles)
    return [{"name": status, "value": count} for status, count in marital_status_counts.items()]


def get_hobbies(profiles):
    all_hobbies = []
    for profile in profiles:
        if profile.hobbies and profile.hobbies != 'N/A':  # Check if hobbies field is not empty
            hobbies = [hobby.strip() for hobby in profile.hobbies.split(',')]
            all_hobbies.extend(hobbies)
    
    hobby_counts = Counter(all_hobbies)
    
    if not hobby_counts:
        return {
            "indicator": [],
            "data": [{
                "value": [],
                "name": "Interest Percentage"
            }]
        }
    
    top_hobbies = hobby_counts.most_common(15)
    
    total_hobby_mentions = sum(count for _, count in top_hobbies)
    hobby_percentages = [
        (hobby, (count / total_hobby_mentions) * 100) 
        for hobby, count in top_hobbies
    ]

    max_percentage = max(percentage for _, percentage in hobby_percentages)
    amplification_factor = 100 / max_percentage if max_percentage > 0 else 1
    
    amplified_percentages = [
        (hobby, percentage * amplification_factor)
        for hobby, percentage in hobby_percentages
    ]
    
    return {
        "indicator": [{"name": hobby, "max": 100} for hobby, _ in amplified_percentages],
        "data": [{
            "value": [percentage for _, percentage in amplified_percentages],
            "name": "Interest Percentage"
        }]
    }