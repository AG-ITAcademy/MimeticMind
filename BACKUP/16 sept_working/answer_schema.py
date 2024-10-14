# schemas.py

from pydantic import BaseModel, Field
from typing import Literal, List

# 1. Scale (1-5)
class ScaleSchema(BaseModel):
    rating: int

# 2. Open-ended
class OpenEndedSchema(BaseModel):
    response: str

# 3. Multiple Choice
class MultipleChoiceSchema(BaseModel):
    choice: str

# 4. Yes/No
class YesNoSchema(BaseModel):
    answer: str

# 5. Ranking (without minItems constraint)
class RankingSchema(BaseModel):
    ranking: list[str]

# Define the schema mapping
schema_mapping = {
    "ScaleSchema": ScaleSchema,
    "OpenEndedSchema": OpenEndedSchema,
    "MultipleChoiceSchema": MultipleChoiceSchema,
    "YesNoSchema": YesNoSchema,
    "RankingSchema": RankingSchema
}