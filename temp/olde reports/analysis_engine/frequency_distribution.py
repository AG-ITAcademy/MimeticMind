# analysis_engine/frequency_distribution.py

from .base import AnalysisMethod
from collections import Counter
from schemas.answer_schemas import schema_mapping

class FrequencyDistribution(AnalysisMethod):
    def __init__(self):
        self.results = {}

    def analyze(self, data, schema):
        if schema not in schema_mapping:
            print(f"Schema {schema} not recognized.")
            return
        schema_class = schema_mapping[schema]
        field_name = list(schema_class.__fields__.keys())[0]
        raw_values = [item[field_name] for item in data if field_name in item]
        
        # Check if the field is a list
        if isinstance(raw_values, list) and all(isinstance(elem, list) for elem in raw_values):
            # Flatten the list of lists
            values = [element for sublist in raw_values for element in sublist]
        else:
            values = raw_values

        frequency_distribution = dict(Counter(values))
        self.results['frequency_distribution'] = frequency_distribution

    def get_results(self):
        return self.results