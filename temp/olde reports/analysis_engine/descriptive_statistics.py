# analysis_engine/descriptive_statistics.py

from .base import AnalysisMethod
import numpy as np
from schemas.answer_schemas import schema_mapping

class DescriptiveStatistics(AnalysisMethod):
    def __init__(self):
        self.results = {}

    def analyze(self, data, schema):
        if schema not in schema_mapping:
            print(f"Schema {schema} not recognized.")
            return
        schema_class = schema_mapping[schema]
        field_name = list(schema_class.__fields__.keys())[0]
        values = [item[field_name] for item in data if field_name in item]
        if not values:
            print(f"No valid data found for field '{field_name}' in schema '{schema}'.")
            return
        self.results['mean'] = np.mean(values)
        self.results['median'] = np.median(values)
        self.results['mode'] = max(set(values), key=values.count)
        self.results['std_dev'] = np.std(values)

    def get_results(self):
        return self.results
