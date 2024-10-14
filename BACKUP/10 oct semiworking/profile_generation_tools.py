### profile_generation.py - Functions to generate the profiles using weights and conditional probabilities from the database

import datetime
import random
from sqlalchemy import text
from profile import Profile  # Import the Profile dataclass

def generate_profile(session):
    # Generate the profile data as before
    profile_data = {}
    
    # Basic demographic attributes
    profile_data['gender'] = _select_weighted_value(session, 'gender')
    profile_data['birth_date'] = _generate_birth_date(session)
    profile_data['ethnicity'] = _select_weighted_value(session, 'ethnicity')

    age = datetime.datetime.now().year - profile_data['birth_date'].year
    age_interval = _get_age_interval(profile_data['birth_date'])
    
    # Determine education level based on age and ethnicity
    profile_data['education_level'] = _select_weighted_value_with_conditions(
        session, 'education_level',
        age_interval=age_interval,
        ethnicity=profile_data['ethnicity']
    )

    # Set occupation
    if age < 16:
        profile_data['occupation'] = 'Unemployed'
    else:
        profile_data['occupation'] = _select_weighted_value_with_conditions(
            session, 'occupation',
            education_level=profile_data['education_level']
        )

    # Determine income range
    profile_data['income_range'] = _select_weighted_value_with_conditions(
        session, 'income_range',
        occupation=profile_data['occupation'],
        ethnicity=profile_data['ethnicity'],
        gender=profile_data['gender']
    )

    # Other attributes
    profile_data['location'] = _select_weighted_value(session, 'location')
    profile_data['health_status'] = _select_correlated_value(session, 'age_interval', 'health_status', age_interval)
    profile_data['legal_status'] = _select_weighted_value(session, 'legal_status')
    profile_data['religion'] = _select_correlated_value(session, 'ethnicity', 'religion', profile_data['ethnicity'])
    profile_data['marital_status'] = _select_correlated_value(session, 'age_interval', 'marital_status', age_interval)

    # Personality traits
    profile_data['big_five_ocean_profile'] = _select_weighted_value(session, 'big_five_ocean_profile')
    profile_data['enneagram_profile'] = None  # Enneagram not implemented yet
    profile_data['mbti_profile'] = _select_weighted_value(session, 'mbti_profile')
    
    # Set personal values and hobbies
    if age < 16:
        profile_data['personal_values'] = 'N/A'
    else:
        profile_data['personal_values'] = get_values_based_on_mbti(session, profile_data['mbti_profile'])
    
    if age < 7:
        profile_data['hobbies'] = 'N/A'
    else:
        profile_data['hobbies'] = get_hobbies_based_on_mbti(session, profile_data['mbti_profile'])

    # Create a Profile instance with the generated data
    profile = Profile(
        session=session,
        profile_name=None,  # You can assign a name or leave it as None
        gender=profile_data['gender'],
        birth_date=profile_data['birth_date'],
        location=profile_data['location'],
        education_level=profile_data['education_level'],
        occupation=profile_data['occupation'],
        income_range=profile_data['income_range'],
        health_status=profile_data['health_status'],
        ethnicity=profile_data['ethnicity'],
        legal_status=profile_data['legal_status'],
        religion=profile_data['religion'],
        marital_status=profile_data['marital_status'],
        big_five_ocean_profile=profile_data['big_five_ocean_profile'],
        enneagram_profile=profile_data['enneagram_profile'],
        mbti_profile=profile_data['mbti_profile'],
        personal_values=profile_data['personal_values'],
        hobbies=profile_data['hobbies'],
        llm_persona=None,       
        llm_typical_day=None  
    )

    return profile
    
def _select_weighted_value(session, category):
    query = text("SELECT value, percentage FROM weights WHERE category = :category")
    weights = session.execute(query, {"category": category}).fetchall()

    choices = [row[0] for row in weights]       
    probabilities = [row[1] for row in weights] 
    return random.choices(choices, probabilities)[0]

def _select_weighted_value_with_conditions(session, category, **conditions):
    # Define the specific column names for each category
    category_column_map = {
        'education_level': 'education_level',
        'occupation': 'occupation',
        'income_range': 'income_range'
    }
    
    # Build the condition clauses dynamically based on provided conditions
    condition_clauses = " AND ".join([f"{key} = :{key}" for key in conditions])
    
    # Build the query based on the category and the corresponding column
    query = text(f"""
        SELECT {category_column_map[category]} AS value, percentage
        FROM multivariable_weights
        WHERE category = :category AND {condition_clauses}
    """)
    
    # Add the category to the condition dictionary
    conditions['category'] = category
    
    # Execute the query with conditions
    weights = session.execute(query, conditions).fetchall()

    # Extract choices and probabilities using tuple indexing
    choices = [row[0] for row in weights]        # row[0] corresponds to the 'value'
    probabilities = [row[1] for row in weights]  # row[1] corresponds to the 'percentage'

    # Error handling for cases where no data is returned
    if not choices or not probabilities:
        raise ValueError(f"No valid choices or probabilities found for category '{category}' with conditions {conditions}")
        
    if sum(probabilities) == 0:
        return 'N/A'
    # Return a randomly selected value based on the weights
    return random.choices(choices, probabilities)[0]


def _select_correlated_value(session, correlation_item1, correlation_item2, value_item1):
    query = text("""
        SELECT value_item2, percentage
        FROM correlations
        WHERE correlation_item1 = :correlation_item1
          AND correlation_item2 = :correlation_item2
          AND value_item1 = :value_item1
    """)
    
    correlations = session.execute(query, {
        "correlation_item1": correlation_item1,
        "correlation_item2": correlation_item2,
        "value_item1": value_item1
    }).fetchall()

    choices = [row[0] for row in correlations]
    probabilities = [row[1] for row in correlations]

    if not choices or not probabilities:
        raise ValueError(f"No valid correlated values found for '{correlation_item1}' and '{correlation_item2}' with value '{value_item1}'")

    return random.choices(choices, probabilities)[0]
    
def get_hobbies_based_on_mbti(session, mbti_profile):    
    # Query the correlations table for hobbies associated with the mbti_profile
    query = text("""
        SELECT value_item2 AS hobby, percentage
        FROM correlations
        WHERE correlation_item1 = 'mbti_profile'
        AND correlation_item2 = 'hobby'
        AND value_item1 = :mbti_profile
    """)
    
    result = session.execute(query, {'mbti_profile': mbti_profile}).fetchall()
    
    if not result:
        return ""
    
    # Extract hobbies and their corresponding percentages using tuple indexing
    hobbies = [row[0] for row in result]        # row[0] corresponds to 'hobby'
    percentages = [row[1] for row in result]    # row[1] corresponds to 'percentage'
    
    # Choose 1 to 4 hobbies based on the weights (percentages)
    num_hobbies = random.randint(1, 4)
    selected_hobbies = random.choices(hobbies, weights=percentages, k=num_hobbies)
    
    # Return the hobbies as a string separated by commas
    return ', '.join(selected_hobbies)
    
def get_values_based_on_mbti(session, mbti_profile): 
    # Query the correlations table for values associated with the mbti_profile
    query = text("""
        SELECT value_item2 AS value, percentage
        FROM correlations
        WHERE correlation_item1 = 'mbti_profile'
        AND correlation_item2 = 'value'
        AND value_item1 = :mbti_profile
    """)
    
    result = session.execute(query, {'mbti_profile': mbti_profile}).fetchall()
    
    if not result:
        return ""
    
    # Extract values and their corresponding percentages using tuple indexing
    values = [row[0] for row in result]        # row[0] corresponds to 'value'
    percentages = [row[1] for row in result]   # row[1] corresponds to 'percentage'
    
    # Select top 3 values based on the weights (percentages)
    selected_values = random.choices(values, weights=percentages, k=3)
    
    # Return the values as a string separated by commas
    return ', '.join(selected_values)


def _get_age_interval(birth_date):
    age = datetime.datetime.now().year - birth_date.year
    intervals = [(0, 1, '0-1'), (2, 5, '2-4'), (6, 15, '5-14'), (16, 24, '15-24'),
                 (25, 34, '25-34'), (35, 44, '35-44'), (45, 54, '45-54'), 
                 (55, 64, '55-64'), (65, 75, '65-75'), (76, 85, '75-85'), 
                 (86, 100, '85-100'), (101, 110, '100-110')]

    for start, end, label in intervals:
        if start <= age <= end:
            return label
    return 'Unknown'

def _generate_birth_date(session):
    """
    Generates a random birth date based on weighted age intervals from the database.
    """
    age_interval = _select_weighted_value(session, 'age_interval')
    age_min, age_max = map(int, age_interval.split('-'))
    birth_year = datetime.datetime.now().year - random.randint(age_min, age_max)
    birth_date = datetime.date(birth_year, random.randint(1, 12), random.randint(1, 28))
    return birth_date


