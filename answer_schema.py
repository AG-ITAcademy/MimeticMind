# answer_schema.py

from pydantic import BaseModel
from typing import List, Dict

class ScaleSchema(BaseModel):
    rating: int

class OpenEndedSchema(BaseModel):
    response: str

class MultipleChoiceSchema(BaseModel):
    choice: str

class YesNoSchema(BaseModel):
    answer: str

class RankingSchema(BaseModel):
    ranking: List[str]

# Define the schema mapping
schema_mapping = {
    "ScaleSchema": ScaleSchema,
    "OpenEndedSchema": OpenEndedSchema,
    "MultipleChoiceSchema": MultipleChoiceSchema,
    "YesNoSchema": YesNoSchema,
    "RankingSchema": RankingSchema
}

# ANALYSIS_METHODS with descriptions and corresponding SQL syntax
preffix = "gender, occupation, income_range, education_level"
condition = " WHERE query_template_id = :question_id AND profile_id IN :profile_ids AND project_survey_id= :project_survey_id"
frequency_distribution_fileds="COUNT(*) as total, COUNT(*) FILTER (WHERE gender = 'Male') as male, COUNT(*) FILTER (WHERE gender = 'Female') as female, COUNT(*) FILTER (WHERE marital_status = 'Single') as single, COUNT(*) FILTER (WHERE marital_status = 'Married') as married, COUNT(*) FILTER (WHERE marital_status = 'Divorced') as divorced, COUNT(*) FILTER (WHERE marital_status = 'Widowed') as widowed, COUNT(*) FILTER (WHERE marital_status = 'Separated') as separated, COUNT(*) FILTER (WHERE health_status = 'Excellent') as health_excellent, COUNT(*) FILTER (WHERE health_status = 'Very Good') as health_very_good, COUNT(*) FILTER (WHERE health_status = 'Good') as health_good, COUNT(*) FILTER (WHERE health_status = 'Fair') as health_fair, COUNT(*) FILTER (WHERE health_status = 'Poor') as health_poor, COUNT(*) FILTER (WHERE income_range = '1 - Low') as income_low, COUNT(*) FILTER (WHERE income_range = '2 - Medium') as income_medium, COUNT(*) FILTER (WHERE income_range = '3 - High') as income_high, COUNT(*) FILTER (WHERE education_level = '1 - Less than High School Diploma') as edu_less_than_hs, COUNT(*) FILTER (WHERE education_level = '2 - High School Graduate') as edu_hs_graduate, COUNT(*) FILTER (WHERE education_level = '3 - Associate Degree') as edu_associate, COUNT(*) FILTER (WHERE education_level = '4 - Bachelor Degree') as edu_bachelor, COUNT(*) FILTER (WHERE education_level = '5 - Master or PhD') as edu_master_phd "

mean_rank_fields="ROUND(AVG(rank), 2) AS total,ROUND(AVG(CASE WHEN gender = 'Male' THEN rank END), 2) AS male,ROUND(AVG(CASE WHEN gender = 'Female' THEN rank END), 2) AS female,ROUND(AVG(CASE WHEN marital_status = 'Single' THEN rank END), 2) AS single,ROUND(AVG(CASE WHEN marital_status = 'Married' THEN rank END), 2) AS married,ROUND(AVG(CASE WHEN marital_status = 'Divorced' THEN rank END), 2) AS divorced,ROUND(AVG(CASE WHEN marital_status = 'Widowed' THEN rank END), 2) AS widowed,ROUND(AVG(CASE WHEN marital_status = 'Separated' THEN rank END), 2) AS separated,ROUND(AVG(CASE WHEN health_status = 'Excellent' THEN rank END), 2) AS health_excellent,ROUND(AVG(CASE WHEN health_status = 'Very Good' THEN rank END), 2) AS health_very_good,ROUND(AVG(CASE WHEN health_status = 'Good' THEN rank END), 2) AS health_good,ROUND(AVG(CASE WHEN health_status = 'Fair' THEN rank END), 2) AS health_fair,ROUND(AVG(CASE WHEN health_status = 'Poor' THEN rank END), 2) AS health_poor,ROUND(AVG(CASE WHEN income_range = '1 - Low' THEN rank END), 2) AS income_low,ROUND(AVG(CASE WHEN income_range = '2 - Medium' THEN rank END), 2) AS income_medium,ROUND(AVG(CASE WHEN income_range = '3 - High' THEN rank END), 2) AS income_high,ROUND(AVG(CASE WHEN education_level = '1 - Less than High School Diploma' THEN rank END), 2) AS edu_less_than_hs,ROUND(AVG(CASE WHEN education_level = '2 - High School Graduate' THEN rank END), 2) AS edu_hs_graduate,ROUND(AVG(CASE WHEN education_level = '3 - Associate Degree' THEN rank END), 2) AS edu_associate,ROUND(AVG(CASE WHEN education_level = '4 - Bachelor Degree' THEN rank END), 2) AS edu_bachelor,ROUND(AVG(CASE WHEN education_level = '5 - Master or PhD' THEN rank END), 2) AS edu_master_phd"

ANALYSIS_METHODS = {  
    "ScaleSchema": {
        "raw_sql": f"SELECT {preffix},'N/A' as item, rating as response FROM vw_scale_responses{condition} ORDER BY {preffix},item",
        "methods": [
            {
                "name": "Descriptive Statistics",
                "description": "Summarizes data using measures like mean, median, mode, and standard deviation to provide an overview of central tendency and dispersion.",
                "chart_type": "boxplot",
                "chart_sql": f"SELECT min(rating) as min, max(rating) as max, round(avg(rating)) as avg FROM vw_scale_responses{condition} ORDER BY 1"
            },
            {
                "name": "Frequency Distribution",
                "description": "Shows how often each response option was selected, helping identify the most common responses.",
                "chart_type": "bar",
                "chart_sql": f"SELECT rating AS response, {frequency_distribution_fileds} FROM vw_scale_responses{condition} GROUP BY rating ORDER BY rating"
            }
        ]
    },
    "OpenEndedSchema": {
        "raw_sql": f"SELECT {preffix},'N/A' as item, response FROM vw_open_ended_responses{condition} ORDER BY {preffix},item",
        "methods": [
            {
                "name": "Sentiment Analysis",
                "description": "Analyzes textual data to determine the emotional tone (positive, negative, neutral) using natural language processing techniques.",
                "chart_type": "pie",
                "chart_sql": f"SELECT response FROM vw_open_ended_responses{condition}" 
            },
            {
                "name": "Word Frequency",
                "description": "Counts the frequency of words or phrases in textual data to identify commonly mentioned topics.",
                "chart_type": "bar",
                "chart_sql": f"SELECT response FROM vw_open_ended_responses{condition}" 
            }
        ]
    },
    "MultipleChoiceSchema": {
        "raw_sql": f"SELECT {preffix},'N/A' as item, choice as response FROM vw_multiple_choice_responses{condition} ORDER BY {preffix},item",
        "methods": [
            {
                "name": "Frequency Distribution",
                "description": "Shows how often each response option was selected, helping identify the most common responses.",
                "chart_type": "bar",
                "chart_sql": f"SELECT choice AS response, {frequency_distribution_fileds} FROM vw_multiple_choice_responses {condition} GROUP BY choice ORDER BY choice"
            },
            {
                "name": "Cluster Analysis",
                "description": "Groups respondents into clusters based on similar responses or characteristics to identify segments within the data.",
                "chart_type": "scatter",
                "chart_sql": f"SELECT EXTRACT(YEAR FROM AGE(CURRENT_DATE, birth_date)) AS age, choice FROM vw_multiple_choice_responses{condition}"  # asta trebuie regandit, momentan coreleaza varsta cu raspunsul
            }
        ]
    },
    "YesNoSchema": {
        "raw_sql": f"SELECT {preffix},'N/A' as item, answer as response FROM vw_yes_no_responses{condition} ORDER BY {preffix},item",
        "methods": [
            {
                "name": "Frequency Distribution",
                "description": "Shows how often each response option was selected, helping identify the most common responses.",
                "chart_type": "pie",
                "chart_sql": f"SELECT answer AS response, {frequency_distribution_fileds} FROM vw_yes_no_responses{condition} GROUP BY answer ORDER BY answer"
            }
        ]
    },
    "RankingSchema": {              
        "raw_sql": f"SELECT {preffix},item, round(avg(rank)) AS response FROM vw_ranking_responses{condition} GROUP BY {preffix},item ORDER BY 6",
        "methods": [
            {
                "name": "Mean Rank Calculation",
                "description": "Calculates the average rank assigned to each item in ranking questions to determine overall preferences.",
                "chart_type": "bar",
                "chart_sql": f"SELECT item, {mean_rank_fields} FROM vw_ranking_responses{condition} GROUP BY item ORDER by 1"
            },
            {
                "name": "Frequency Distribution",
                "description": "Shows how often each response option was selected, helping identify the most common responses.",
                "chart_type": "bar",
                "chart_sql": f"SELECT item AS response, {frequency_distribution_fileds} FROM vw_ranking_responses{condition} GROUP BY item ORDER BY item"
            }
        ]
    }
}

def get_data_from_schema(schema):
    return ANALYSIS_METHODS.get(schema, None)
