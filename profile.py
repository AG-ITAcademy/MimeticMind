from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from models import ProfileModel, QueryTemplate , Population, LLM, User
from openai import OpenAI
from groq import Groq
import instructor
from answer_schema import schema_mapping, MultipleChoiceSchema, OpenEndedSchema, YesNoSchema, ScaleSchema, RankingSchema, schema_mapping
from pydantic import BaseModel
import json
from config import Config
from celery import chord
from celery_app import celery
import redis
import re
from mistralai import Mistral
from llama_index.llms.nvidia import NVIDIA
from llama_index.core.llms import ChatMessage, MessageRole

@celery.task
def query_LLM(messages: str, schema: str, user_id: int, profile_id: int, query_template_id: int, query_text: str, project_survey_id: int, model: str, llm_id: int, base_url: str, api_key: str, summary: str, query:str):
    messages_obj = json.loads(messages)
    schema_class = schema_mapping.get(schema)
    
    if llm_id==0:
        client = OpenAI(base_url=base_url, api_key=api_key)  
        response = client.beta.chat.completions.parse(
            model=model,
            temperature=1,
            messages=messages_obj,
            response_format=schema_class
        )
        content = response.choices[0].message.content.lower()
        prompt_tokens = response.usage.prompt_tokens
        completion_tokens = response.usage.completion_tokens
        
    elif llm_id==1:
        client = client = Mistral(api_key=api_key)
        response = client.chat.complete(
            model= model, 
            messages=messages_obj,
            response_format = {"type": "json_object"}
        )
        prompt_tokens=0
        completion_tokens=0

        content=response.choices[0].message.content.lower()
        
    elif llm_id==2:
        LLM = NVIDIA(base_url=base_url, api_key=api_key, model=model, temperature=1)  
        LLM = LLM.as_structured_llm (output_cls=schema_class)
        messages = [
            ChatMessage(role=MessageRole.SYSTEM, content=(f"You will assume the following identity: {summary}\n\n")),
            ChatMessage(role=MessageRole.ASSISTANT, content=("Adapt your vocabulary, knowledge level and language style to the assumed identity. Try to mimick the assumed identity as accurate as possible, ignoring your own biased opinion about the topic. \n")),
            ChatMessage(role=MessageRole.USER, content=(f"Answer in English to the following query without adding any other details: {query}.\n"), ),
        ]
        content = str(LLM.chat(messages))
        content = re.sub(r'^assistant:\s*', '', content.lower())
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

    def enqueue_query(self, user_id: int, profile_id: int, query: str, schema: str, query_template_id: int, project_survey_id: int) -> str:
        # Fetch the profile's population tag
        population_tag = self.session.query(ProfileModel.tags).filter_by(id=profile_id).scalar()
        
        # Fetch the prompt template from the populations table
        prompt_template = self.get_population_prompt_template(population_tag)

        # Get user's LLM settings
        user = self.session.query(User).get(user_id)
        llm = self.session.query(LLM).get(user.llm_id)
        model = llm.settings
        
        # Summarize the profile's attributes
        summary = self.summarize_attributes()
        
        # Replace placeholders in the prompt template with summary and query values
        for message in prompt_template:
            message['content'] = message['content'].replace("{summary}", summary).replace("{query}", query)
        
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
            llm.base_url,
            llm.api_key,
            summary,
            query
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
