### generate_n_profiles.py script that generates and saves N profiles

from profile_generation_tools import generate_profile  # Assuming the generation logic is in profile_generation.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Setup SQLAlchemy connection and session
DATABASE_URL = "postgresql://postgres:the bad zone@localhost/postgres" 
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

# Number of profiles to generate
N = 1000  # Set N to the desired number of profiles

# Generate and save N profiles
for _ in range(N):
    # Generate a Profile instance
    profile = generate_profile(session)
    
    # Optional: proces with LLM
    
    # Save the profile to the database
    profile_id = profile.save_to_db()
    print(f"Profile saved with ID: {profile_id}")

# Close the session after use
session.close()
