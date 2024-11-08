import json

#  prompts used in various modules

survey_generation_instructions = '''A survey consists of:
- Title (short title, suggestive for the survey type)
- Description (clear description of the survey objectives)
- Survey questions (between 3 and 8) questions. Each question has this format: question_text, possible_answers, schema.  The schema can have the following values:
      ScaleSchema - answer can be on a scale from 1 to 5 (make sure to explain the values in the question text)
      OpenEndedSchema - answer is open-ended
      MultipleChoiceSchema - answer is a single choice from several options
      YesNoSchema - answer can be Yes or No
      RankingSchema: example: -  the answer consists of an ordered list of options (make sure to explain the order meaning in the question text)
You are free to decide on the apropriate number of questions and schema for each question. 
If the user query is not compatible with your task you must always return the answer "Inadequate description!"
Provide the response in valid JSON format with fields: survey_title, survey_description, and survey_questions array.'''


survey_generation_messages = json.dumps([
    {
        "role": "system",
        "content": "You are an expert AI Assistant integrated within the MimeticMind application. This application can be used to generate various types of surveys that can be run against a customizable population of AI responders."
    },
    {
        "role": "assistant",
        "content": "The current user does not have the necessary skills to build an effective survey. Your task is to create a survey for them based on their query."
    },
    {
        "role": "assistant",
        "content": survey_generation_instructions
    },
    {
        "role": "user",
        "content": "The user query is: "
    }
])




