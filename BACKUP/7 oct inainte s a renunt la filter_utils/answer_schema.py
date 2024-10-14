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

# Updated ANALYSIS_METHODS with descriptions
ANALYSIS_METHODS = {
    "ScaleSchema": [
        {
            "name": "Descriptive Statistics",
            "description": "Summarizes data using measures like mean, median, mode, and standard deviation to provide an overview of central tendency and dispersion.",
            "chart_type": "Box Plot"
        },
        {
            "name": "Frequency Distribution",
            "description": "Shows how often each response option was selected, helping identify the most common responses.",
            "chart_type": "Histogram"
        }
    ],
    "OpenEndedSchema": [
        {
            "name": "Sentiment Analysis",
            "description": "Analyzes textual data to determine the emotional tone (positive, negative, neutral) using natural language processing techniques.",
            "chart_type": "Pie Chart"
        },
        {
            "name": "Word Frequency",
            "description": "Counts the frequency of words or phrases in textual data to identify commonly mentioned topics.",
            "chart_type": "Word Cloud"
        }
    ],
    "MultipleChoiceSchema": [
        {
            "name": "Frequency Distribution",
            "description": "Shows how often each response option was selected, helping identify the most common responses.",
            "chart_type": "Bar Chart"
        },
        {
            "name": "Cluster Analysis",
            "description": "Groups respondents into clusters based on similar responses or characteristics to identify segments within the data.",
            "chart_type": "Scatter Plot"
        }
    ],
    "YesNoSchema": [
        {
            "name": "Frequency Distribution",
            "description": "Shows how often each response option was selected, helping identify the most common responses.",
            "chart_type": "Pie Chart"
        }
    ],
    "RankingSchema": [
        {
            "name": "Mean Rank Calculation",
            "description": "Calculates the average rank assigned to each item in ranking questions to determine overall preferences.",
            "chart_type": "Horizontal Bar Chart"
        },
        {
            "name": "Frequency Distribution",
            "description": "Shows how often each response option was selected, helping identify the most common responses.",
            "chart_type": "Stacked Bar Chart"
        }
    ]
}

def get_analysis_methods(schema_type: str) -> List[Dict[str, str]]:
    return ANALYSIS_METHODS.get(schema_type, [])

def get_chart_type(schema_type: str, analysis_method: str) -> str:
    methods = ANALYSIS_METHODS.get(schema_type, [])
    for method in methods:
        if method['name'] == analysis_method:
            return method['chart_type']
    return "No chart type found"