# analysis_engine/mean_rank_calculation.py

from .base import AnalysisMethod
import numpy as np
from schemas.answer_schemas import schema_mapping
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MeanRankCalculation(AnalysisMethod):
    def __init__(self):
        self.results = {}

    def analyze(self, data, schema):
        if schema not in schema_mapping:
            logger.warning(f"Schema {schema} not recognized.")
            return
        schema_class = schema_mapping[schema]
        field_name = list(schema_class.__fields__.keys())[0]
        rank_dict = {}
        for item in data:
            ranking = item.get(field_name, [])
            if not isinstance(ranking, list):
                logger.warning(f"Expected list for field '{field_name}', got {type(ranking)}")
                continue
            for rank, value in enumerate(ranking, start=1):
                if value not in rank_dict:
                    rank_dict[value] = []
                rank_dict[value].append(rank)
        if rank_dict:
            mean_rank = {item: np.mean(ranks) for item, ranks in rank_dict.items()}
            self.results['mean_rank'] = mean_rank
        else:
            self.results['mean_rank'] = {}
            logger.warning("No ranking data available to calculate mean ranks.")

    def get_results(self):
        return self.results
