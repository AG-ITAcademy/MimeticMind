# schemas/answer_schemas.py

from pydantic import BaseModel
from typing import List

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

# Schema mapping
schema_mapping = {
    "ScaleSchema": ScaleSchema,
    "OpenEndedSchema": OpenEndedSchema,
    "MultipleChoiceSchema": MultipleChoiceSchema,
    "YesNoSchema": YesNoSchema,
    "RankingSchema": RankingSchema
}
