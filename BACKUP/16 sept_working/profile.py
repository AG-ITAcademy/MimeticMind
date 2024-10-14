from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from profile_model import ProfileModel
from template import QueryTemplate  
from openai import OpenAI
from answer_schema import schema_mapping
from pydantic import BaseModel

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

    def answer_query(self, session_id: int, profile_id: int, query: str, template: QueryTemplate) -> str:
        """Answer a query using a predefined query template."""
        summary = self.summarize_attributes()
        schema_class = schema_mapping.get(template.schema)

        client = OpenAI()  
        response = client.beta.chat.completions.parse(
            model="gpt-4o-2024-08-06",  
            messages=[
                {"role": "system", "content": f"You will assume the following identity: {summary}\n\n"},
                {"role": "assistant", "content": "Adapt your language, technical knowledge and style to the persona. Don't mention your personality traits in your response.\n"},
                {"role": "user", "content": f"Answer the following query: {query}.\n"}
            ],
            response_format=schema_class 
        )
        
        answer = response.choices[0].message.content
        prompt_tokens = response.usage.prompt_tokens
        completion_tokens = response.usage.completion_tokens

        # Log the interaction by calling the private method
        self._log_interaction(session_id, profile_id, query, str(answer), template.id, prompt_tokens + completion_tokens)

        return answer


    def _log_interaction(self, session_id: int, profile_id: int, query_text: str, answer_text: str, template_id: int, cost: int, timestamp=None) -> None:
        """Private method to log an interaction into the interactions table."""
        query_cost = cost

        interaction_insert_query = text("""
            INSERT INTO interactions (session_id, profile_id, query_text, answer_text, query_cost, template_id, interaction_timestamp)
            VALUES (:session_id, :profile_id, :query_text, :answer_text, :query_cost, :template_id, :interaction_timestamp)
        """)

        timestamp = timestamp or datetime.now()

        self.session.execute(interaction_insert_query, {
            'session_id': session_id,
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
