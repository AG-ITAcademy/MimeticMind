### profile_generation.py - Functions to generate the profiles using weights and conditional probabilities from the database

import datetime
import random
from sqlalchemy import text
from profile import Profile

def generate_profile(session):
    # Generate the profile data as before
    profile_data = {}
    
    # Basic demographic attributes
    profile_data['gender'] = _select_weighted_value(session, 'gender')
    profile_data['birth_date'] = _generate_birth_date(session)
    profile_data['ethnicity'] = _select_weighted_value(session, 'ethnicity')

    age = datetime.datetime.now().year - profile_data['birth_date'].year
    age_interval = _get_age_interval(profile_data['birth_date'])
    
    # Determine education level based on age 
    profile_data['education_level'] = _select_correlated_value(
        session, 
        'age_interval',
        'education_level', 
        age_interval
    )

    # Query general income distribution from BLS table for fallback cases
    income_query = text("""
        SELECT DISTINCT income_range, 
               COUNT(*) OVER (PARTITION BY income_range) * 100.0 / COUNT(*) OVER () as percentage
        FROM _bls_jobs_us
        GROUP BY income_range
        ORDER BY percentage DESC
    """)
    income_ranges = session.execute(income_query).fetchall()
    ranges = [row[0] for row in income_ranges]
    weights = [float(row[1]) for row in income_ranges]

    # Set occupation and get OCEAN profile
    if age < 16:
        profile_data['occupation'] = 'N/A'
        adjusted_weights = []
        for range_val, weight in zip(ranges, weights):
            if '1 - Low' in range_val:
                adjusted_weights.append(weight * 0.5)
            elif '2 - Medium' in range_val:
                adjusted_weights.append(weight * 1.8)
            else:
                adjusted_weights.append(weight * 0.8)
        
        # Normalize weights
        total = sum(adjusted_weights)
        adjusted_weights = [w/total for w in adjusted_weights]
        
        profile_data['income_range'] = random.choices(ranges, weights=adjusted_weights, k=1)[0]
        profile_data['big_five_ocean_profile'] = '33333'  # Default OCEAN
    elif age >= 66:
        profile_data['occupation'] = 'Retired'
        # Adjust weights to favor middle income for retirees
        adjusted_weights = []
        for range_val, weight in zip(ranges, weights):
            if '2 - Medium' in range_val:
                adjusted_weights.append(weight * 1.9)  # Increase middle income more
            elif '1 - Low' in range_val:
                adjusted_weights.append(weight * 0.6)  # Decrease low income more
            else:
                adjusted_weights.append(weight * 0.9)  # Keep high income similar
                
        # Normalize weights
        total = sum(adjusted_weights)
        adjusted_weights = [w/total for w in adjusted_weights]
        
        profile_data['income_range'] = random.choices(ranges, weights=adjusted_weights, k=1)[0]
        profile_data['big_five_ocean_profile'] = '33333'  # Default OCEAN
    else:
        # Extract education level number from the string (e.g., "5 - Bachelor Degree" -> 5)
        education_number = int(profile_data['education_level'].split('-')[0].strip())
        
        # Query jobs that match or are below the person's education level
        query = text("""
            SELECT occ_job, percentage, income_range, ocean
            FROM _bls_jobs_us
            WHERE :education_level >= minimum_education__level
            AND percentage > 0
        """)
        
        jobs = session.execute(query, {"education_level": education_number}).fetchall()
        
        # Extract jobs and their probabilities
        job_choices = [row[0] for row in jobs]
        job_probabilities = [float(row[1]) for row in jobs]
        income_ranges = [row[2] for row in jobs]
        ocean_profiles = [row[3] for row in jobs]
        
        # Select job based on percentages
        selected_index = random.choices(range(len(job_choices)), weights=job_probabilities, k=1)[0]
        
        profile_data['occupation'] = job_choices[selected_index]
        profile_data['income_range'] = income_ranges[selected_index]
        profile_data['big_five_ocean_profile'] = str(ocean_profiles[selected_index])

    # Other attributes
    profile_data['location'] = _select_weighted_value(session, 'location')
    profile_data['health_status'] = _select_correlated_value(session, 'age_interval', 'health_status', age_interval)
    profile_data['legal_status'] = _select_weighted_value(session, 'legal_status')
    profile_data['religion'] = _select_correlated_value(session, 'ethnicity', 'religion', profile_data['ethnicity'])
    profile_data['marital_status'] = _select_correlated_value(session, 'age_interval', 'marital_status', age_interval)

    # Personality traits
    if profile_data['big_five_ocean_profile'] == None:
        profile_data['big_five_ocean_profile'] = _select_weighted_value(session, 'big_five_ocean_profile')
    profile_data['children'] = get_number_of_children(age, profile_data['marital_status'])
    profile_data['mbti_profile'] = get_mbti_from_ocean(profile_data['big_five_ocean_profile'])
    
    # Set personal values and hobbies
    if age < 18:
        profile_data['personal_values'] = 'N/A'
    else:
        profile_data['personal_values'] = get_values_based_on_ocean(session, profile_data['big_five_ocean_profile'], age)
    
    if age < 18:
        profile_data['hobbies'] = 'N/A'
    else:
        profile_data['hobbies'] = get_hobbies_based_on_ocean(session, profile_data['big_five_ocean_profile'], age)

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
        children=profile_data['children'],
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


def get_hobbies_based_on_ocean(session, ocean_profile, age):
    if age < 18:
        return 'N/A'
        
    def is_hobby_compatible(hobby, ocean_profile):
        # Each OCEAN score is 1-5, where:
        # O (Openness): 1=conventional, 5=innovative
        # C (Conscientiousness): 1=spontaneous, 5=organized
        # E (Extraversion): 1=introverted, 5=extroverted
        # A (Agreeableness): 1=challenging, 5=agreeable
        # N (Neuroticism): 1=confident, 5=sensitive

        o, c, e, a, n = [int(x) for x in ocean_profile]

        incompatible_matches = {
            "Socializing": {"E": [1], "A": [1]},  # Very introverted or disagreeable unlikely to have socializing as hobby
            "Dancing": {"E": [1]},  # Very introverted unlikely to enjoy dancing
            "Volunteering": {"A": [1, 2], "E": [1]},  # Low agreeableness or very introverted unlikely to volunteer
            "Tech/Computers": {"O": [1]},  # Very conventional might avoid tech
            "Writing": {"O": [1]},  # Very conventional unlikely to write creatively
            "Drawing/Painting": {"O": [1]},  # Very conventional unlikely to do creative arts
            "Playing Musical Instruments": {"O": [1]},  # Very conventional unlikely to play music
            "Meditation": {"O": [1], "E": [5]},  # Very conventional or very extroverted unlikely to meditate
            "Yoga": {"O": [1]},  # Very conventional unlikely to do yoga
            "Blogging/Vlogging": {"O": [1], "E": [1]},  # Very conventional or introverted unlikely to blog
            "Sports": {"E": [1]},  # Very introverted unlikely to do team sports
            "Board Games/Card Games": {"A": [1], "E": [1]},  # Very disagreeable or introverted unlikely to play social games
            "DIY Arts & Crafts": {"O": [1]},  # Very conventional unlikely to do creative crafts
            "Bird Watching": {"E": [5]},  # Very extroverted unlikely to do solitary watching
            "Reading": {"O": [1], "E": [5]},  # Very conventional or very extroverted unlikely to read much
            "Knitting/Crocheting": {"O": [1]},  # Very conventional unlikely to do crafts
        }

        if hobby in incompatible_matches:
            for trait, incompatible_values in incompatible_matches[hobby].items():
                trait_index = "OCEAN".index(trait)
                trait_value = int(ocean_profile[trait_index])
                if trait_value in incompatible_values:
                    return False
        return True

    # Get hobbies and their weights
    query = text("""
        SELECT value, percentage 
        FROM weights 
        WHERE category = 'hobbies'
    """)
    
    hobby_data = session.execute(query).fetchall()
    
    # Filter out incompatible hobbies
    compatible_hobbies = [(hobby, float(pct)) for hobby, pct in hobby_data 
                         if is_hobby_compatible(hobby, ocean_profile)]
    
    if not compatible_hobbies:
        return "No specific hobbies"
        
    hobbies, weights = zip(*compatible_hobbies)
    
    # Select 1-4 unique hobbies based on weights
    num_hobbies = random.randint(1, min(4, len(compatible_hobbies)))
    
    # Use random.choices for the first selection with weights
    # Then remove the selected hobby and adjust the weights for subsequent selections
    selected_hobbies = []
    remaining_hobbies = list(hobbies)
    remaining_weights = list(weights)
    
    for _ in range(num_hobbies):
        if not remaining_hobbies:
            break
        selected_index = random.choices(range(len(remaining_hobbies)), 
                                     weights=remaining_weights, k=1)[0]
        selected_hobbies.append(remaining_hobbies[selected_index])
        remaining_hobbies.pop(selected_index)
        remaining_weights.pop(selected_index)
    
    return ", ".join(selected_hobbies)
    
    
def get_values_based_on_ocean(session, ocean_profile, age):
    if age < 16:
        return 'N/A'
        
    def is_value_compatible(value, ocean_profile):
        o, c, e, a, n = [int(x) for x in ocean_profile]
        
        # Define value compatibility based on OCEAN scores
        incompatible_matches = {
            "Self-Direction": {"O": [1], "A": [5], "C": [5]},  # Low openness or high agreeableness/conscientiousness
            "Stimulation": {"O": [1], "N": [5], "C": [5]},     # Low openness, high neuroticism or conscientiousness
            "Hedonism": {"C": [5], "N": [5]},                  # High conscientiousness or neuroticism
            "Achievement": {"C": [1], "E": [1]},               # Low conscientiousness or extraversion
            "Power": {"A": [5], "N": [5]},                     # High agreeableness or neuroticism
            "Security": {"O": [5], "N": [1]},                  # High openness or low neuroticism
            "Conformity": {"O": [5], "E": [5]},                # High openness or extraversion
            "Tradition": {"O": [5]},                           # High openness
            "Benevolence": {"A": [1], "E": [1]},               # Low agreeableness or extraversion
            "Universalism": {"O": [1], "A": [1]}               # Low openness or agreeableness
        }

        if value in incompatible_matches:
            for trait, incompatible_values in incompatible_matches[value].items():
                trait_index = "OCEAN".index(trait)
                trait_value = int(ocean_profile[trait_index])
                if trait_value in incompatible_values:
                    return False
        return True

    # Define values with their base percentages
    values_data = [
        ("Self-Direction", 0.12),
        ("Stimulation", 0.08),
        ("Hedonism", 0.10),
        ("Achievement", 0.12),
        ("Power", 0.06),
        ("Security", 0.11),
        ("Conformity", 0.09),
        ("Tradition", 0.08),
        ("Benevolence", 0.14),
        ("Universalism", 0.10)
    ]
    
    # Filter out incompatible values
    compatible_values = [(value, float(pct)) for value, pct in values_data 
                        if is_value_compatible(value, ocean_profile)]
    
    if not compatible_values:
        return "No specific values"
        
    values, weights = zip(*compatible_values)
    
    # Select 3 values based on weights
    selected = random.choices(values, weights=weights, k=min(3, len(values)))
    return ", ".join(selected)
    
    
def get_mbti_from_ocean(ocean_profile):
    """Convert OCEAN scores to MBTI type.
    
    E/I: primarily from E score
    S/N: primarily from O score
    T/F: from combination of A and N scores
    J/P: primarily from C score with O influence
    """
    o, c, e, a, n = [int(x) for x in ocean_profile]
    
    # E/I - Extraversion 
    # High E (4-5) = E, Low E (1-2) = I, Mid (3) = weighted random
    ei = 'E' if e >= 4 else 'I' if e <= 2 else random.choices(['E', 'I'], weights=[0.5, 0.5])[0]
    
    # S/N - Openness
    # High O (4-5) = N, Low O (1-2) = S, Mid (3) = weighted random
    sn = 'N' if o >= 4 else 'S' if o <= 2 else random.choices(['S', 'N'], weights=[0.6, 0.4])[0]
    
    # T/F - Combination of Agreeableness and Neuroticism
    # High A or High N tends toward F
    # Low A and Low N tends toward T
    tf_score = (a + n) / 2
    tf = 'F' if tf_score >= 3.5 else 'T' if tf_score <= 2.5 else random.choices(['T', 'F'], weights=[0.5, 0.5])[0]
    
    # J/P - Primarily Conscientiousness with Openness influence
    # High C and Low O strongly suggests J
    # Low C or High O suggests P
    jp_score = c - (o - 3)  # Adjust C based on O's deviation from middle
    jp = 'J' if jp_score >= 3.5 else 'P' if jp_score <= 2.5 else random.choices(['J', 'P'], weights=[0.5, 0.5])[0]
    
    return f"{ei}{sn}{tf}{jp}"
    
    
def get_number_of_children(age, marital_status):
    """
    Determine number of children based on demographic factors.
    
    Age groups considerations:
    - Under 18: No children
    - 18-24: Rare, mostly 0-1
    - 25-34: Common childbearing years, 0-2
    - 35-44: Peak number of children, 0-3
    - 45-65: Grown children period, 0-4
    - Over 65: Historical larger families, 0-5
    
    Marital status impacts:
    - Single: Lower probability
    - Married: Highest probability
    - Divorced: Medium probability
    - Widowed: Based on age group
    """
    
    if age < 18:
        return 0
        
    # Define probabilities for each age group and marital status
    age_group_probabilities = {
        (18, 24): {
            'Single': {'weights': [0.95, 0.05], 'max_children': 1},
            'Married': {'weights': [0.70, 0.25, 0.05], 'max_children': 2},
            'Divorced': {'weights': [0.90, 0.10], 'max_children': 1},
            'Widowed': {'weights': [0.95, 0.05], 'max_children': 1}
        },
        (25, 34): {
            'Single': {'weights': [0.80, 0.15, 0.05], 'max_children': 2},
            'Married': {'weights': [0.30, 0.40, 0.20, 0.10], 'max_children': 3},
            'Divorced': {'weights': [0.60, 0.30, 0.10], 'max_children': 2},
            'Widowed': {'weights': [0.70, 0.20, 0.10], 'max_children': 2}
        },
        (35, 44): {
            'Single': {'weights': [0.70, 0.20, 0.08, 0.02], 'max_children': 3},
            'Married': {'weights': [0.15, 0.35, 0.30, 0.15, 0.05], 'max_children': 4},
            'Divorced': {'weights': [0.40, 0.35, 0.20, 0.05], 'max_children': 3},
            'Widowed': {'weights': [0.40, 0.35, 0.20, 0.05], 'max_children': 3}
        },
        (45, 65): {
            'Single': {'weights': [0.75, 0.15, 0.08, 0.02], 'max_children': 3},
            'Married': {'weights': [0.10, 0.30, 0.35, 0.20, 0.05], 'max_children': 4},
            'Divorced': {'weights': [0.30, 0.40, 0.25, 0.05], 'max_children': 3},
            'Widowed': {'weights': [0.20, 0.40, 0.30, 0.10], 'max_children': 3}
        },
        (66, 100): {
            'Single': {'weights': [0.70, 0.20, 0.08, 0.02], 'max_children': 3},
            'Married': {'weights': [0.05, 0.25, 0.40, 0.25, 0.05], 'max_children': 4},
            'Divorced': {'weights': [0.20, 0.40, 0.30, 0.10], 'max_children': 3},
            'Widowed': {'weights': [0.10, 0.30, 0.40, 0.20], 'max_children': 3}
        }
    }

    # Find appropriate age group
    current_age_group = None
    for (min_age, max_age) in age_group_probabilities.keys():
        if min_age <= age <= max_age:
            current_age_group = (min_age, max_age)
            break
    
    if current_age_group is None or marital_status not in age_group_probabilities[current_age_group]:
        return 0
        
    probs = age_group_probabilities[current_age_group][marital_status]
    weights = probs['weights']
    max_children = probs['max_children']
    
    # Generate possible numbers of children (0 to max_children)
    possible_children = list(range(max_children + 1))
    
    # Select number of children based on weights
    return random.choices(possible_children, weights=weights, k=1)[0]