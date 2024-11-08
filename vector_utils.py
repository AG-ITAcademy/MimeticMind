#vector_utils.py

"""
Vector search implementation using NVIDIA embeddings for semantic profile matching.
Provides similarity search across profile data using embedding comparisons.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from llama_index.embeddings.nvidia import NVIDIAEmbedding
import numpy as np
from models import ProfileModel, ProfileView, LLM
from collections import defaultdict
from config import Config
from typing import List 

# Could not use Llamaindex's PGVectorStore features because pgvector is not supported on Postgress17 and I'm using Windows on my dev environment :(
class VectorSearch:
    """Handles semantic search over profile data using NVIDIA embeddings."""
    def __init__(
        self,
        embedding_model: str = "nvidia/llama-3.2-nv-embedqa-1b-v1",
    ):
        self.engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
        self.Session = sessionmaker(bind=self.engine)
        
        # Get API key from database
        session = self.Session()
        try:
            llm = session.query(LLM).filter_by(id=0).first()
            if not llm or not llm.api_key:
                raise ValueError("Could not find API key in database")
            api_key = llm.api_key
        finally:
            session.close()
            
        self.embedder = NVIDIAEmbedding(model=embedding_model, api_key=api_key)

    def find_similar_profiles_from_query(
            self, 
            query: str,
            base_query,
            similarity_threshold: float = 0.5,
        ) -> List[int]:
            """
            Find similar profiles from a pre-filtered query.
            
            Args:
                query: Search query text
                base_query: Pre-filtered SQLAlchemy query (from ProfileView)
                similarity_threshold: Minimum similarity score (0-1) to include in results
            """
            # Create a new clean query just for IDs from ProfileView
            clean_base_query = base_query.with_entities(ProfileView.id)
            matching_profile_ids = [p[0] for p in clean_base_query.all()]
            
            if not matching_profile_ids:
                return []
                
            query_embedding = self.embedder.get_text_embedding(query)
            
            session = self.Session()
            try:
                # Now query ProfileModel with these IDs to get vector data
                profiles = session.query(ProfileModel).filter(
                    ProfileModel.id.in_(matching_profile_ids),
                    (ProfileModel.llm_persona_embeddings.isnot(None)) |
                    (ProfileModel.llm_typical_day_embeddings.isnot(None))
                ).all()
                
                profile_scores = defaultdict(float)
                
                for profile in profiles:
                    # Process persona chunks
                    if profile.llm_persona_chunks and profile.llm_persona_embeddings:
                        for embedding in profile.llm_persona_embeddings:
                            similarity = self.cosine_similarity(query_embedding, embedding)
                            if similarity >= similarity_threshold:
                                profile_scores[profile.id] += similarity
                    
                    # Process typical day chunks
                    if profile.llm_typical_day_chunks and profile.llm_typical_day_embeddings:
                        for embedding in profile.llm_typical_day_embeddings:
                            similarity = self.cosine_similarity(query_embedding, embedding)
                            if similarity >= similarity_threshold:
                                profile_scores[profile.id] += similarity
                
                sorted_profiles = sorted(
                    profile_scores.items(),
                    key=lambda x: x[1],
                    reverse=True
                )
                
                return [profile_id for profile_id, score in sorted_profiles if score > 0]
                
            finally:
                session.close()
            
    @staticmethod
    def cosine_similarity(embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings"""
        embedding1 = np.array(embedding1)
        embedding2 = np.array(embedding2)
        return np.dot(embedding1, embedding2) / (
            np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
        )

