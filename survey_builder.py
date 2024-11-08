#survey_builder.py

"""
Blueprint for survey creation and management functionality.
Handles survey CRUD operations, AI-based survey generation, and template management.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import Project, db, Population, SurveyTemplate, ProjectSurvey, QueryTemplate, User, LLM
from sqlalchemy.orm import joinedload
from flask_wtf.csrf import CSRFProtect
from flask import jsonify
from answer_schema import schema_mapping
from forms import SurveyForm
from config_prompts import survey_generation_messages
import json
from llama_index.llms.nvidia import NVIDIA
from llama_index.llms.mistralai import MistralAI
from llama_index.llms.openai import OpenAI
from llama_index.core.llms import ChatMessage, MessageRole
from pydantic import BaseModel
from typing import List

survey_builder_bp = Blueprint('survey_builder_bp', __name__)
csrf = CSRFProtect()

@survey_builder_bp.route('/survey/create')
@login_required
def create_survey():
    """Display survey creation page with available projects, populations and templates."""
    
    projects = Project.query.filter_by(user_id=current_user.id, status='active').all()
    populations = Population.query.all()
    templates = SurveyTemplate.query.all()  # This will include both default and user-defined templates
    return render_template('survey_create.html', projects=projects, populations=populations, templates=templates)

@survey_builder_bp.route('/surveys')
@login_required
def list_surveys():
    """Show list of user's survey templates with their associated projects."""
    
    survey_templates = SurveyTemplate.query.filter_by(user_id=current_user.id).options(
        joinedload(SurveyTemplate.project_surveys).joinedload(ProjectSurvey.project)
    ).all()
    return render_template('survey_edit.html', survey_templates=survey_templates)

@survey_builder_bp.route('/survey/edit/<int:template_id>')
@login_required
def edit_survey(template_id):
    """Load survey template editor."""
    
    survey_template = SurveyTemplate.query.get_or_404(template_id)
    if survey_template.user_id and survey_template.user_id != current_user.id:
        flash('You do not have permission to edit this survey template.', 'danger')
        return redirect(url_for('survey_builder_bp.list_surveys'))
    form = SurveyForm(obj=survey_template)
    form.survey_id.data = survey_template.id  # Explicitly set the survey_id
    schema_options = list(schema_mapping.keys()) if schema_mapping else []
    return render_template('survey_builder.html', form=form, survey=survey_template, schema_options=schema_options)

@survey_builder_bp.route('/survey/delete/<int:template_id>', methods=['POST'])
@login_required
def delete_survey(template_id):
    """Delete survey template."""
    
    survey_template = SurveyTemplate.query.get_or_404(template_id)
    if not survey_template.user_id or survey_template.user_id != current_user.id:
        flash('You do not have permission to delete this survey template.', 'danger')
        return redirect(url_for('survey_builder_bp.list_surveys'))
    
    db.session.delete(survey_template)
    db.session.commit()
    flash('Survey template has been deleted.', 'success')
    return redirect(url_for('survey_builder_bp.list_surveys'))


@survey_builder_bp.route('/survey/build', methods=['GET', 'POST'])
@login_required
def build_survey():
    """Create new survey, optionally copying from existing template."""
    
    form = SurveyForm()
    template_id = request.args.get('template_id')
    
    if template_id:
        template = SurveyTemplate.query.get_or_404(template_id)
        form = SurveyForm(obj=template)
        survey = SurveyTemplate(
            name=f"Copy of {template.name}",
            description=template.description,
            context_prompt=template.context_prompt,
            user_id=current_user.id
        )
        # Copy query templates
        for query in template.query_templates:
            new_query = QueryTemplate(
                name=query.name,
                query_text=query.query_text,
                schema=query.schema
            )
            survey.query_templates.append(new_query)
    else:
        survey = SurveyTemplate(name="New Survey", user_id=current_user.id)

    # Extract schema options from schema_mapping
    schema_options = list(schema_mapping.keys()) if schema_mapping else []

    return render_template('survey_builder.html', form=form, survey=survey, schema_options=schema_options)
    
    
@survey_builder_bp.route('/survey/save', methods=['POST'])
@login_required
def save_survey():
    """Save new or update existing survey template and its queries."""
    data = request.json
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    survey_id = data.get('survey_id')
    
    if survey_id:
        # Updating an existing survey
        survey = SurveyTemplate.query.get_or_404(survey_id)
        if survey.user_id != current_user.id:
            return jsonify({'error': 'You do not have permission to edit this survey.'}), 403
    else:
        # Creating a new survey
        survey = SurveyTemplate(user_id=current_user.id)
        db.session.add(survey)
    
    # Update or set survey details
    survey.name = data.get('name', 'Untitled Survey')
    survey.description = data.get('description')
    survey.context_prompt = data.get('context_prompt')
    
    # Process queries
    updated_queries = []
    
    for query_data in data.get('query_templates', []):
        query_id = query_data.get('id')
        if query_id:
            # Update existing query
            query = QueryTemplate.query.get(query_id)
            if query:
                query.name = 'Untitled Query'
                query.query_text = query_data.get('query_text')
                query.schema = query_data.get('schema')
                updated_queries.append(query)
        else:
            # Add new query
            new_query = QueryTemplate(
                name= 'Untitled Query',
                query_text=query_data.get('query_text'),
                schema=query_data.get('schema')
            )
            updated_queries.append(new_query)
    
    # Update the survey's query templates
    survey.query_templates = updated_queries
    
    try:
        db.session.commit()
        flash("Survey saved successfully!", "success")
        return jsonify({'message': 'Survey saved successfully', 'survey_id': survey.id}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
   

class SurveyQuestion(BaseModel):
    """Pydantic model for structured survey question data."""
    
    question_text: str
    possible_answers: str
    answer_schema: str

class SurveyResponse(BaseModel):
    """Pydantic model for complete AI-generated survey structure."""
    
    survey_title: str
    survey_description: str
    survey_questions: List[SurveyQuestion]

@survey_builder_bp.route('/survey/generate', methods=['POST'])
@login_required
def generate_survey():
    """Generate survey using AI based on user description."""
    
    description = request.form.get('survey-description', '')  
    if not description:
        flash('Please provide a survey description.', 'error')
        return redirect(url_for('survey_builder_bp.create_survey'))
    
    try:
        user = User.query.get(current_user.id)
        llm_settings = LLM.query.get(user.llm_id)

        # Initialize appropriate LLM based on user settings
        if llm_settings.id == 0:  
            llm = NVIDIA(api_key=llm_settings.api_key, model=llm_settings.settings, temperature=1)
        elif llm_settings.id == 1:  
            llm = MistralAI(api_key=llm_settings.api_key, model=llm_settings.settings, temperature=1)
        else: 
            llm = OpenAI(api_key=llm_settings.api_key, model=llm_settings.settings, temperature=1)
            
        llm = llm.as_structured_llm(output_cls=SurveyResponse)
        
        messages = json.loads(survey_generation_messages)
        messages[-1]["content"] = f"The user query is: {description}"
        
        # Convert messages to ChatMessage format
        chat_messages = [
            ChatMessage(
                role=MessageRole.SYSTEM if msg["role"] == "system" else 
                     MessageRole.ASSISTANT if msg["role"] == "assistant" else 
                     MessageRole.USER,
                content=msg["content"]
            ) for msg in messages
        ]

        prompt_str = llm.messages_to_prompt(chat_messages)
        response = llm.complete(prompt_str)
        
        print('*****************************')
        print(response)
        print('*****************************')
        
        # Check if the description was inadequate
        if isinstance(response, str) and "Inadequate description" in response:
            flash('Inadequate description. Please retry!', 'error')
            return redirect(url_for('survey_builder_bp.create_survey'))
        
        response_obj = response.raw
        # Create the form and survey with AI-generated content
        form = SurveyForm()
        form.name.data = response_obj.survey_title
        form.description.data = response_obj.survey_description
        form.context_prompt.data = "AI Assistant generated survey - Feel free to modify this context prompt according to your needs."
        
        survey = SurveyTemplate(
            name=form.name.data,
            description=form.description.data,
            context_prompt=form.context_prompt.data,
            user_id=current_user.id
        )
        
        # Add the AI-generated questions
        for question in response_obj.survey_questions:
            query = QueryTemplate(
                name=question.question_text,
                query_text=f"{question.question_text}...{question.possible_answers}",
                schema=question.answer_schema
            )
            survey.query_templates.append(query)
        
        schema_options = list(schema_mapping.keys()) if schema_mapping else []
        return render_template('survey_builder.html', form=form, survey=survey, schema_options=schema_options, source='ai')
        
    except json.JSONDecodeError as e:
        flash('An error occurred while processing your request. The response was not in the expected format.', 'error')
        print(f"JSON Decode Error: {e}")
        return redirect(url_for('survey_builder_bp.create_survey'))
        
    except Exception as e:
        flash('An unexpected error occurred while generating your survey. Please try again.', 'error')
        print(f"Error: {e}")
        return redirect(url_for('survey_builder_bp.create_survey'))