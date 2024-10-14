# analysis_engine/cluster_analysis.py

from .base import AnalysisMethod
from sklearn.cluster import KMeans
import numpy as np
from schemas.answer_schemas import schema_mapping
import logging
from sklearn.preprocessing import LabelEncoder

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ClusterAnalysis(AnalysisMethod):
    def __init__(self):
        self.results = {}

    def analyze(self, data, schema):
        if schema not in schema_mapping:
            logger.warning(f"Schema {schema} not recognized.")
            return
        schema_class = schema_mapping[schema]
        field_name = list(schema_class.__fields__.keys())[0]
        values = [item[field_name] for item in data if field_name in item]
        if not values:
            logger.warning(f"No valid data found for field '{field_name}' in schema '{schema}'.")
            return
        try:
            if schema == "ScaleSchema":
                X = np.array(values).reshape(-1, 1).astype(float)
            elif schema == "RankingSchema":
                flattened_values = [item for sublist in values for item in sublist]
                le = LabelEncoder()
                X = le.fit_transform(flattened_values).reshape(-1, 1)
            else:
                le = LabelEncoder()
                X = le.fit_transform(values).reshape(-1, 1)
            kmeans = KMeans(n_clusters=3, random_state=42)
            kmeans.fit(X)
            self.results['clusters'] = kmeans.labels_.tolist()
            self.results['cluster_centers'] = kmeans.cluster_centers_.flatten().tolist()
        except Exception as e:
            logger.error(f"Error performing KMeans clustering: {e}")

    def get_results(self):
        return self.results
