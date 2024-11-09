#config_prompts.py
'''  prompts used for AI assisted building building of surveys '''

import json

survey_generation_instructions = '''A survey consists of:
- Title (short title, suggestive for the survey type)
- Description (clear description of the survey objectives)
- Survey questions (between 3 and 8) questions.  The answer schema for each question can be one of the following:
      - ScaleSchema - answer can be on a scale from 1 to 5 (make sure to explain the values in the question text)
      - OpenEndedSchema - answer is open-ended
      - MultipleChoiceSchema - answer is a single choice from several options
      - YesNoSchema - answer can be Yes or No
      - RankingSchema -  the answer is an ordered list of options (make sure to explain the order meaning in the question text)
You are free to decide on the apropriate number of questions and schema for each question. 
If the user query is not compatible with your task you must always return the answer "Inadequate description!"
Provide the response in the required JSON format.'''


survey_generation_messages = [
    {
        "role": "system",
        "content": "You are an expert AI Assistant integrated within the MimeticMind application. This application can be used to generate various types of surveys that can be run against a customizable population of AI responders."
    },
    {
        "role": "assistant",
        "content": "Your task is to create a survey for the users based on their query by following these instructions: " + survey_generation_instructions
    },
    {
        "role": "user",
        "content": "The user query is: {query}"
    }
]
