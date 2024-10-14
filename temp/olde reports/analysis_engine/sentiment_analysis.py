# analysis_engine/sentiment_analysis.py

from .base import AnalysisMethod
from textblob import TextBlob
from schemas.answer_schemas import schema_mapping
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SentimentAnalysis(AnalysisMethod):
    def __init__(self):
        self.results = {}

    def analyze(self, data, schema):
        if schema not in schema_mapping:
            logger.warning(f"Schema {schema} not recognized.")
            return
        schema_class = schema_mapping[schema]
        field_name = list(schema_class.__fields__.keys())[0]
        sentiments = []
        for item in data:
            if field_name in item:
                response = item[field_name]
                blob = TextBlob(response)
                sentiments.append(blob.sentiment.polarity)
            else:
                logger.warning(f"Field '{field_name}' not found in data item: {item}")
        if sentiments:
            self.results['average_sentiment'] = sum(sentiments) / len(sentiments)
            self.results['sentiments'] = sentiments
        else:
            self.results['average_sentiment'] = None
            self.results['sentiments'] = []
            logger.warning("No sentiments were analyzed due to missing data.")

    def get_results(self):
        return self.results
