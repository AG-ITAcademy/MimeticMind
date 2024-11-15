#filter_utils.py
"""
Utility functions and form definitions for filtering profile data.
Handles form population, query filtering, and segment creation.
"""

from flask_wtf import FlaskForm
from wtforms import IntegerField, SelectField
from wtforms.validators import Optional
from models import ProfileView, db
from sqlalchemy import and_, or_
from datetime import datetime, timedelta

def populate_filter_form_choices(form, population_tag=None):
    """
    Populate the choices for select fields in the filter form.
    """
    query_filter = ProfileView.tags.contains(population_tag) if population_tag else True
    
    # Helper function to get distinct values
    def get_distinct_values(field):
        return [('Any', 'Any')] + [(v[0], v[0]) for v in db.session.query(field).filter(query_filter).distinct().order_by(field)]

    form.gender.choices = get_distinct_values(ProfileView.gender)
    form.location.choices = get_distinct_values(ProfileView.location)
    form.ethnicity.choices = get_distinct_values(ProfileView.ethnicity)
    form.occupation.choices = get_distinct_values(ProfileView.occupation)
    form.education_level.choices = get_distinct_values(ProfileView.education_level)
    form.religion.choices = get_distinct_values(ProfileView.religion)
    form.health_status.choices = get_distinct_values(ProfileView.health_status)
    form.legal_status.choices = get_distinct_values(ProfileView.legal_status)
    form.marital_status.choices = get_distinct_values(ProfileView.marital_status)
    form.income_range.choices = [('Any', 'Any'), ('1 - Low', 'Low'), ('2 - Medium', 'Medium'), ('3 - High', 'High')]


def apply_filters_to_query(query, form_data):
    """
    Apply filters to the given query based on form data.
    """
    filters = []

    if form_data.get('gender') and form_data['gender'] != 'Any':
        filters.append(ProfileView.gender == form_data['gender'])
    
    if form_data.get('age_min'):
        filters.append(ProfileView.birth_date <= (datetime.now() - timedelta(days=365*int(form_data['age_min']))))
    
    if form_data.get('age_max'):
        filters.append(ProfileView.birth_date >= (datetime.now() - timedelta(days=365*int(form_data['age_max']))))
    
    for field in ['location', 'ethnicity', 'occupation', 'education_level', 'religion', 'health_status', 'legal_status', 'marital_status']:
        if form_data.get(field) and form_data[field] != 'Any':
            filters.append(getattr(ProfileView, field).ilike(f"%{form_data[field]}%"))
    
    if form_data.get('income_range') and form_data['income_range'] != 'Any':
        income_filter = or_(
            ProfileView.income_range.ilike(f"%{form_data['income_range']}%"),
            ProfileView.income_range == form_data['income_range']
        )
        filters.append(income_filter)

    return query.filter(and_(*filters))



def get_filtered_profiles(population_tag, form_data):
    """
    Get filtered profiles based on population tag and form data.
    """
    query = ProfileView.query
    if population_tag:
        query = query.filter(ProfileView.tags.contains(population_tag))
    return apply_filters_to_query(query, form_data)


# FilterForm e duplicat aproape cu cel din forms.py care e folosit la segmente


class FilterForm(FlaskForm):
    """
    Form for filtering in Population Explorer and Survey Analysis. Does not include alias.
    """
    gender = SelectField('Gender', validators=[Optional()])
    age_min = IntegerField('Age Min', validators=[Optional()])
    age_max = IntegerField('Age Max', validators=[Optional()])
    location = SelectField('Location', validators=[Optional()])
    ethnicity = SelectField('Ethnicity', validators=[Optional()])
    occupation = SelectField('Occupation', validators=[Optional()])
    education_level = SelectField('Education Level', validators=[Optional()])
    religion = SelectField('Religion', validators=[Optional()])
    health_status = SelectField('Health Status', validators=[Optional()])
    legal_status = SelectField('Legal Status', validators=[Optional()])
    marital_status = SelectField('Marital Status', validators=[Optional()])
    income_range = SelectField('Income Range', validators=[Optional()], choices=[('Low', 'Low'), ('Medium', 'Medium'), ('High', 'High')])



def create_segment_from_form(project_id, form_data):
    """
    Create a new segment (FilterModel) from form data.
    """
    from models import FilterModel  # to avoid circular imports
    
    new_filter = FilterModel(
        project_id=project_id,
        alias=form_data['alias'],
        gender=form_data['gender'] if form_data['gender'] != 'Any' else None,
        age_min=form_data['age_min'],
        age_max=form_data['age_max'],
        location=form_data['location'] if form_data['location'] != 'Any' else None,
        ethnicity=form_data['ethnicity'] if form_data['ethnicity'] != 'Any' else None,
        occupation=form_data['occupation'] if form_data['occupation'] != 'Any' else None,
        education_level=form_data['education_level'] if form_data['education_level'] != 'Any' else None,
        religion=form_data['religion'] if form_data['religion'] != 'Any' else None,
        health_status=form_data['health_status'] if form_data['health_status'] != 'Any' else None,
        legal_status=form_data['legal_status'] if form_data['legal_status'] != 'Any' else None,
        marital_status=form_data['marital_status'] if form_data['marital_status'] != 'Any' else None,
        income_range=form_data['income_range'] if form_data['income_range'] != 'Any' else None,
        ai_filter= form_data['ai_filter'] if form_data['ai_filter'] else None
    )
    db.session.add(new_filter)
    db.session.commit()
    return new_filter