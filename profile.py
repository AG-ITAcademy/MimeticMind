#profile.py

"""
Profile management and LLM interaction module.
The module uses Celery for asynchronous task processing and Redis for progress tracking.
"""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from models import ProfileModel, Population, LLM, User
from answer_schema import schema_mapping
import json
from config import Config
from celery_app import celery
import redis
from llama_index.llms.nvidia import NVIDIA
from llama_index.llms.mistralai import MistralAI
from llama_index.llms.openai import OpenAI
from llama_index.core.llms import ChatMessage, MessageRole

@celery.task
def query_LLM(messages: str, schema: str, user_id: int, profile_id: int, query_template_id: int, query_text: str, project_survey_id: int, model: str, llm_id: int, api_key: str, summary: str, query:str, survey_description:str, survey_context:str):
    messages_obj = json.loads(messages)
    schema_class = schema_mapping.get(schema)
    
    system_prompt = next(item["content"] for item in messages_obj if item["role"] == "system").format(summary=summary)
    assistant_prompt = next(item["content"] for item in messages_obj if item["role"] == "assistant"). format(description=survey_description, context=survey_context)
    user_prompt = next(item["content"] for item in messages_obj if item["role"] == "user").format(query=query)
    messages = [ChatMessage(role=MessageRole.SYSTEM, content=(system_prompt)), ChatMessage(role=MessageRole.ASSISTANT, content=(assistant_prompt)), ChatMessage(role=MessageRole.USER, content=(user_prompt), )]
       
    if llm_id==0:
        LLM = NVIDIA(api_key=api_key, model=model, temperature=1)  
    elif llm_id==1:
        LLM = MistralAI(api_key=api_key, model=model, temperature=1)  
    elif llm_id==2:
        LLM = OpenAI(api_key=api_key, model=model, temperature=1) 

    LLM = LLM.as_structured_llm (output_cls=schema_class)
    prompt_str = LLM.messages_to_prompt(messages)
    content = str(LLM.complete(prompt_str)).lower()    
        
    # token counters - to be implemented later    
    prompt_tokens =0
    completion_tokens =0

    # After task completion, update progress in Redis
    r = redis.Redis(host=Config.REDIS_HOST, port=Config.REDIS_PORT, db=Config.REDIS_DB)
    r.incr(f"survey_completed_tasks_{project_survey_id}")
    
    return content, prompt_tokens, completion_tokens, user_id, profile_id, query_template_id, query_text, project_survey_id


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
    children: Optional[int] = None
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
            children=self.children,
            mbti_profile=self.mbti_profile,
            personal_values=self.personal_values,
            hobbies=self.hobbies,
            llm_persona=self.llm_persona,
            llm_typical_day=self.llm_typical_day
        )
        self.session.add(profile_record)
        self.session.commit()
        return profile_record.id
        
    @staticmethod
    def ocean_profile_to_string(ocean_code):
        levels = {1: "Very Low", 2: "Low", 3: "Medium", 4: "High", 5: "Very High"}
        traits = ["Openness", "Conscientiousness", "Extraversion", "Agreeableness", "Non-Negativity"]
        
        ocean_code_str = str(ocean_code)
        if len(ocean_code_str) != 5 or not ocean_code_str.isdigit():
            raise ValueError("Input must be a 5-digit number with each digit from 1 to 5.")
        
        return ", ".join(f"{traits[i]}={levels[int(digit)]}" for i, digit in enumerate(ocean_code_str))

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
            + (f"Children: {self.children}\n" if self.children > 0 else "") +
            f"Big Five OCEAN Profile: {self.ocean_profile_to_string(self.big_five_ocean_profile)}\n"
            f"Ethnicity: {self.ethnicity}\n"
            f"Legal Status: {self.legal_status}\n"
            f"Health Status: {self.health_status}\n"
        )

        if age > 16:
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

        summary+= (
            f"Detailed profile: {self.llm_persona}\n"
            f"Typical day: {self.llm_typical_day}\n"
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

    def enqueue_query(self, user_id: int, profile_id: int, query: str, schema: str, query_template_id: int, project_survey_id: int, survey_description:str, survey_context:str) -> str:
        # Fetch the profile's population tag
        population_tag = self.session.query(ProfileModel.tags).filter_by(id=profile_id).scalar()
        
        # Fetch the prompt template from the populations table
        prompt_template = self.get_population_prompt_template(population_tag)

        # Get user's LLM settings
        user = self.session.query(User).get(user_id)
        llm = self.session.query(LLM).get(user.llm_id)
        model = llm.settings
        
        # summarize attributes
        summary = self.summarize_attributes()
               
        task_signature = query_LLM.s(
            json.dumps(prompt_template),  
            str(schema),
            user_id,
            profile_id,
            query_template_id,
            query,
            project_survey_id,
            model,          
            user.llm_id,
            llm.api_key,
            summary,
            query,
            survey_description, 
            survey_context
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
           children=model.children,
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
