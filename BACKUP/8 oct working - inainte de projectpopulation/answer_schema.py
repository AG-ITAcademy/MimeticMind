# answer_schema.py

from pydantic import BaseModel
from typing import List, Dict

# Keep the original classes
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
ANALYSIS_METHODS = {  ############ la toate chart_sql trebuie aplicat filtru dupa profile_ids !!!!!!!!!!!!!!!!!!!!!!!!!!!!!
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
                "chart_sql": f"SELECT rating AS response, count(*) as frequency FROM vw_scale_responses{condition} GROUP BY rating ORDER BY 1"
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
                "chart_sql": f"SELECT response FROM vw_open_ended_responses{condition}" # asta trebuie procesat suplimentar !!!!!!!!!!!
            },
            {
                "name": "Word Frequency",
                "description": "Counts the frequency of words or phrases in textual data to identify commonly mentioned topics.",
                "chart_type": "bar",
                "chart_sql": f"SELECT response FROM vw_open_ended_responses{condition}" # asta trebuie procesat suplimentar !!!!!!!!!!!
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
                "chart_sql": f"SELECT choice AS response, count(*) as frequency FROM vw_multiple_choice_responses{condition} GROUP BY choice ORDER BY choice"
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
                "chart_sql": f"SELECT answer AS response, count(*) as frequency FROM vw_yes_no_responses{condition} GROUP BY answer ORDER BY answer"
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
                "chart_sql": f"SELECT item, ROUND(AVG(rank), 1) AS mean_rank FROM vw_ranking_responses{condition} GROUP BY item ORDER by mean_rank"
            },
            {
                "name": "Frequency Distribution",
                "description": "Shows how often each response option was selected, helping identify the most common responses.",
                "chart_type": "bar",
                "chart_sql": f"SELECT item AS response, count(*) as frequency FROM vw_ranking_responses{condition} GROUP BY item ORDER by item"
            }
        ]
    }
}

def get_data_from_schema(schema):
    return ANALYSIS_METHODS.get(schema, None)
