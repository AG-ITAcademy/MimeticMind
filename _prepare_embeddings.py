from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy import Float, Text
from llama_index.core import Document
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.nvidia import NVIDIAEmbedding
from models import ProfileModel
import numpy as np

# Database connection
DATABASE_URL = "postgresql://postgres:the bad zone@localhost/postgres"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

def split_into_paragraphs(text, max_length=1000):
    """
    Split text into paragraphs and ensure each paragraph isn't too long
    """
    if not text:
        return []
    
    # Split on double newlines to get paragraphs
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    
    # Initialize sentence splitter for long paragraphs
    sentence_splitter = SentenceSplitter(chunk_size=max_length, chunk_overlap=50)
    
    final_chunks = []
    for paragraph in paragraphs:
        if len(paragraph) > max_length:
            # If paragraph is too long, split it into sentences
            doc = Document(text=paragraph)
            nodes = sentence_splitter.get_nodes_from_documents([doc])
            final_chunks.extend([node.text for node in nodes])
        else:
            final_chunks.append(paragraph)
    
    # Debug print to see the chunks
    print(f"\nNumber of chunks: {len(final_chunks)}")
    for i, chunk in enumerate(final_chunks):
        print(f"\nChunk {i+1}:")
        print("-" * 40)
        print(chunk)
        print("-" * 40)
    
    return final_chunks

def generate_embeddings():
    # Initialize NVIDIA embedder
    embedder = NVIDIAEmbedding(
        model="nvidia/llama-3.2-nv-embedqa-1b-v1", 
        api_key='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'
    )
    
    # Query profiles without embeddings
    profiles = session.query(ProfileModel).filter(
        ProfileModel.llm_persona_embeddings.is_(None) |
        ProfileModel.llm_typical_day_embeddings.is_(None)
    ).all()
    
    for profile in profiles:
        print(f"\nProcessing profile ID: {profile.id}")
        
        # Process llm_persona
        if profile.llm_persona:
            print("\nProcessing llm_persona:")
            # Split text into paragraphs
            persona_chunks = split_into_paragraphs(profile.llm_persona)
            
            if persona_chunks:
                # Generate embeddings for each chunk using NVIDIA NIM
                persona_embeddings = embedder.get_text_embedding_batch(persona_chunks)
                
                # Store chunks and embeddings directly (they're already lists)
                profile.llm_persona_chunks = persona_chunks
                profile.llm_persona_embeddings = persona_embeddings
                
                # Debug print
                print(f"Stored {len(profile.llm_persona_embeddings)} persona embeddings")
                print(f"First embedding length: {len(profile.llm_persona_embeddings[0])}")
            else:
                profile.llm_persona_chunks = None
                profile.llm_persona_embeddings = None
        
        # Process llm_typical_day
        if profile.llm_typical_day:
            print("\nProcessing llm_typical_day:")
            # Split text into paragraphs
            typical_day_chunks = split_into_paragraphs(profile.llm_typical_day)
            
            if typical_day_chunks:
                # Generate embeddings for each chunk using NVIDIA NIM
                typical_day_embeddings = embedder.get_text_embedding_batch(typical_day_chunks)
                
                # Store chunks and embeddings directly (they're already lists)
                profile.llm_typical_day_chunks = typical_day_chunks
                profile.llm_typical_day_embeddings = typical_day_embeddings
                
                # Debug print
                print(f"Stored {len(profile.llm_typical_day_embeddings)} typical day embeddings")
                print(f"First embedding length: {len(profile.llm_typical_day_embeddings[0])}")
            else:
                profile.llm_typical_day_chunks = None
                profile.llm_typical_day_embeddings = None
        
        # Save changes
        session.commit()
    
    print("\nFinished processing all profiles")

if __name__ == "__main__":
    generate_embeddings()