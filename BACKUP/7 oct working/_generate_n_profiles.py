### generate_n_profiles.py script that generates and saves N profiles

from profile_generation_tools import generate_profile  # Assuming the generation logic is in profile_generation.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from profile_model import Base  # Import Base to create tables if needed

# Setup SQLAlchemy connection and session
DATABASE_URL = "postgresql://postgres:the bad zone@localhost/postgres" 
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

# Create all tables (ensure tables are created)
Base.metadata.create_all(engine)

# Number of profiles to generate
N = 1  # Set N to the desired number of profiles

# Generate and save N profiles
for _ in range(N):
    # Generate a Profile instance
    profile = generate_profile(session)
    
    # Optional: Generate LLM description
    # profile.generate_llm_description()
    
    # Save the profile to the database
    profile_id = profile.save_to_db()
    print(f"Profile saved with ID: {profile_id}")

# Close the session after use
session.close()
