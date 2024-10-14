from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from models import ProfileModel, QueryTemplate , Population
from openai import OpenAI
from answer_schema import schema_mapping
from pydantic import BaseModel
import json
from celery import chord
from celery_app import celery
import redis

@celery.task
def query_LLM (model: str, messages: str, schema: str, user_id: int, profile_id: int, query_template_id: int, query_text: str, project_survey_id: int):
    messages_obj = json.loads(messages)
    schema_class = schema_mapping.get(schema)
    client = OpenAI()  
    response = client.beta.chat.completions.parse(
        model=model,
        messages=messages_obj,
        response_format=schema_class
    )
    
    # After task is processed, update progress in Redis
    r = redis.Redis(
        host=Config.REDIS_HOST,
        port=Config.REDIS_PORT,
        db=Config.REDIS_DB
    )
    
    # Increment completed tasks counter
    completed_tasks = r.incr(f"survey_completed_tasks_{project_survey_id}")
    total_tasks = int(r.get(f"survey_total_tasks_{project_survey_id}"))

    # Calculate and set progress percentage in Redis
    progress = (completed_tasks / total_tasks) * 100
    r.set(f"survey_progress_{project_survey_id}", progress)
    return response.choices[0].message.content, response.usage.prompt_tokens, response.usage.completion_tokens, user_id, profile_id, query_template_id, query_text, project_survey_id


@dataclass
class Profile:
    session: Session
    profile_name: Optional[str] = None
    gender: Optional[str] = None
    birth_date: Optional[date] = None
    location: Optional[str] = None
    education_level: Optional[str] = None
    occupation: Optional[str] = None
    income_range: Optional[str] = None
    health_status: Optional[str] = None
    ethnicity: Optional[str] = None
    legal_status: Optional[str] = None
    religion: Optional[str] = None
    marital_status: Optional[str] = None
    big_five_ocean_profile: Optional[str] = None
    enneagram_profile: Optional[int] = None
    mbti_profile: Optional[str] = None
    personal_values: Optional[str] = None
    hobbies: Optional[str] = None
    llm_persona: Optional[str] = None
    llm_typical_day: Optional[str] = None

    def save_to_db(self) -> int:
        """Save the profile to the database."""
        profile_record = ProfileModel(
            profile_name=self.profile_name,
            gender=self.gender,
            birth_date=self.birth_date,
            location=self.location,
            education_level=self.education_level,
            occupation=self.occupation,
            income_range=self.income_range,
            health_status=self.health_status,
            ethnicity=self.ethnicity,
            legal_status=self.legal_status,
            religion=self.religion,
            marital_status=self.marital_status,
            big_five_ocean_profile=self.big_five_ocean_profile,
            enneagram_profile=self.enneagram_profile,
            mbti_profile=self.mbti_profile,
            personal_values=self.personal_values,
            hobbies=self.hobbies,
            llm_persona=self.llm_persona,
            llm_typical_day=self.llm_typical_day
        )
        self.session.add(profile_record)
        self.session.commit()
        return profile_record.id

    def summarize_attributes(self) -> str:
        """Summarize profile attributes into a string."""
        current_date = datetime.now()
        age = current_date.year - self.birth_date.year - (
            (current_date.month, current_date.day) < (self.birth_date.month, self.birth_date.day)
        )

        summary = (
            f"Gender: {self.gender}\n"
            f"Birth Date: {self.birth_date}\n"
            f"Current Age: {age}\n"
            f"Location: {self.location}\n"
            f"Education Level: {self.education_level}\n"
            f"MBTI Traits: {self.mbti_profile}\n"
            f"Big Five OCEAN Profile: {self.big_five_ocean_profile} - each OCEAN trait is measured on a scale from 1 to 5\n"
            f"Ethnicity: {self.ethnicity}\n"
            f"Legal Status: {self.legal_status}\n"
            f"Health Status: {self.health_status}\n"
        )

        if age > 10:
            summary += (
                f"Occupation: {self.occupation}\n"
                f"Income Range: {self.income_range}\n"
                f"Religion: {self.religion}\n"
                f"Marital Status: {self.marital_status}\n"
                f"Personal Values: {self.personal_values}\n"
                f"Hobbies: {self.hobbies}\n"
            )
        else:
            summary += (
                f"Occupation: Not applicable yet\n"
                f"Parent's Income Range: {self.income_range}\n"
                f"Parent's Religion: {self.religion}\n"
            )

        return summary
        
    def get_population_prompt_template(self, population_tag: str) -> Optional[str]:
        """Fetch the prompt_template for the population tag."""
        population = self.session.query(Population).filter_by(tag=population_tag).first()
        if population and population.prompt_template:
            return population.prompt_template
        else:
            print(f"No prompt_template found for population tag: {population_tag}")
            return None

    def enqueue_query(self, user_id: int, profile_id: int, query: str, schema: str, query_template_id: int, project_survey_id: int) -> str:
        # Fetch the profile's population tag
        population_tag = self.session.query(ProfileModel.tags).filter_by(id=profile_id).scalar()
        
        # Fetch the prompt template from the populations table
        prompt_template = self.get_population_prompt_template(population_tag)

        # Summarize the profile's attributes
        summary = self.summarize_attributes()
        
        # Replace placeholders in the prompt template with summary and query values
        for message in prompt_template:
            message['content'] = message['content'].replace("{summary}", summary).replace("{query}", query)

        print ("querying...")
        
        model = "gpt-4o-mini"  # This model can be customized if needed
        task_signature = query_LLM.s(
            str(model),
            json.dumps(prompt_template),  
            str(schema),
            user_id,
            profile_id,
            query_template_id,
            query,
            project_survey_id
        )
        print(f"Task signature created for query template id: {query_template_id}")

        return task_signature


    def _log_interaction(self, user_id: int, profile_id: int, query_text: str, answer_text: str, template_id: int, cost: int, timestamp=None) -> None:
        """Private method to log an interaction into the interactions table."""
        query_cost = cost
    
        interaction_insert_query = text("""
            INSERT INTO interactions (user_id, profile_id, query_text, answer_text, query_cost, template_id, interaction_timestamp)
            VALUES (:user_id, :profile_id, :query_text, :answer_text, :query_cost, :template_id, :interaction_timestamp)
        """)

        timestamp = timestamp or datetime.now()

        self.session.execute(interaction_insert_query, {
            'user_id': user_id,
            'profile_id': profile_id,
            'query_text': query_text,
            'answer_text': answer_text,
            'query_cost': query_cost,
            'template_id': template_id,
            'interaction_timestamp': timestamp 
        })
        self.session.commit()

    @classmethod
    def from_model(cls, session: Session, model: ProfileModel):
        """Create a Profile object from a ProfileModel instance."""
        return cls(
            session=session,
            profile_name=model.profile_name,
            gender=model.gender,
            birth_date=model.birth_date,
            location=model.location,
            education_level=model.education_level,
            occupation=model.occupation,
            income_range=model.income_range,
            health_status=model.health_status,
            ethnicity=model.ethnicity,
            legal_status=model.legal_status,
            religion=model.religion,
            marital_status=model.marital_status,
            big_five_ocean_profile=model.big_five_ocean_profile,
            enneagram_profile=model.enneagram_profile,
            mbti_profile=model.mbti_profile,
            personal_values=model.personal_values,
            hobbies=model.hobbies,
            llm_persona=model.llm_persona,
            llm_typical_day=model.llm_typical_day
        )
        
    @classmethod
    def from_id(cls, session: Session, profile_id: int):
        """Retrieve a Profile from the database using the given profile_id."""
        profile_record = session.query(ProfileModel).filter_by(id=profile_id).first()
        if profile_record:
            return cls.from_model(session, profile_record)
        return None
