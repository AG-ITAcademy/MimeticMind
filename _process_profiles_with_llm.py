### process_profiles_with_llm.py - processes existing profiles and generates profile_name, llm_persona and llm_typical_day using gpt-4o

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import ProfileModel  
from profile import Profile
from openai import OpenAI
from datetime import datetime

# Setup SQLAlchemy connection and session
DATABASE_URL = "postgresql://postgres:the bad zone@localhost/postgres"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

def _call_llm_for_name_and_persona(prompt):
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that generates a persona name and description.\n"},
            {"role": "assistant", "content": "Always answer with persona full name on the first line (no suffix, prefix or title, just the full name) followed by a long-form, realistic persona description on the next line.\n"},
            {"role": "assistant", "content": "Don't divide the answer into different sections and be relistic, do not always provide happy stories\n "},
            {"role": "user", "content": "Generate a persona name and a description of this persona using all the provided traits and characteristics. Mention just the resulting traits, not the specific characteristics specified in the profile, like MBTI or OCEAN.\. Make sure you cover the most important aspects such as Psychographics, Behavioral patterns, Challenges/Pain points, Goals, Preferred communication channels, Influencers and sources of information, Technological proficiency and Buying triggers. Here is the profile: " + prompt}
        ]
    )
    return response.choices[0].message.content
    
def _call_llm_for_typical_day(prompt):
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that imagines a typical day for a given persona"},
            {"role": "assistant", "content": "The response should provide a description of a typical day, emphasizing the behaviours, usual Challenges/Pain points and habits. The description should not be divided into different sections and should not mention the specific characteristics specified in the profile."},
            {"role": "user", "content": "Generate the story of a typical day for this profile: " + prompt}
        ]
    )
    return response.choices[0].message.content

def _parse_llm_response(llm_response):
    lines = llm_response.strip().split('\n', 1)
    if len(lines) > 1:
        profile_name = lines[0].strip()
        llm_persona = lines[1].strip()
    else:
        llm_persona = llm_response.strip()
        profile_name = None
    return profile_name, llm_persona

def process_profiles(N):
    profiles = session.query(ProfileModel).filter(
        (ProfileModel.llm_persona == None) | (ProfileModel.llm_persona == '')
    ).limit(N).all()
    print(f"Number of profiles: {len(profiles)}")
    
    for profile_record in profiles:
        # Create a Profile instance from the ProfileModel
        profile = Profile.from_model(session, profile_record)
        
        # Use the summarize_attributes method from the Profile class
        attributes_summary = profile.summarize_attributes()
        
        llm_response = _call_llm_for_name_and_persona(attributes_summary)
        profile_name, llm_persona = _parse_llm_response(llm_response)
        profile.llm_persona = llm_persona
        print(f"Persona Description:\n{llm_persona}")
        attributes_summary += "\n\n" + llm_persona
        llm_response = _call_llm_for_typical_day(attributes_summary)
        print(f"\n\nTypical Day:\n{llm_response}")
        profile.llm_typical_day = llm_response
        profile.profile_name = profile_name
        
        # Update the profile_record with new data
        profile_record.llm_persona = profile.llm_persona
        profile_record.llm_typical_day = profile.llm_typical_day
        profile_record.profile_name = profile.profile_name
        session.add(profile_record)
    session.commit()
    
N = 1000
process_profiles(N)

print(f"LLM personas generated and saved for the first {N} profiles.")
