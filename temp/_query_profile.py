from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from profile_model import ProfileModel
from profile import Profile
from template import Template  # Import the Template class

def main(session_id, profile_id, query):
    # Step 1: Setup SQLAlchemy connection and session
    DATABASE_URL = "postgresql://postgres:the bad zone@localhost/postgres"  # Replace with your actual credentials
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Step 2: Retrieve the template with ID 1 from the database
    saved_template = Template.get_by_id(session, 1)

    if not saved_template:
        print("Template with ID 1 not found.")
        session.close()
        return

    # Step 3: Query the profile from the database
    profile_model = session.query(ProfileModel).filter_by(id=profile_id).first()

    if profile_model:
        # Step 4: Convert ProfileModel to Profile
        profile = Profile.from_model(session, profile_model)

        # Step 5: Use the retrieved template in the profile query
        answer = profile.answer_query(session_id, profile_id, query, saved_template)
        print(answer)
    else:
        print(f"No profile found with ID: {profile_id}")

    # Close the session after use
    session.close()

if __name__ == "__main__":
    # Example query and profile ID
    profile_id = 5820  # Replace with actual profile ID
    session_id = 1
    query = 'what is your greatest regret for this year?'

    # Call the main function with template_id = 1
    main(session_id, profile_id, query)

