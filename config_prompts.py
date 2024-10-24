import json

# these are the prompts used in various modules

survey_generation_instructions = '''A survey consists of:
- Title (short title, suggestive for the survey type)
- Description (clear description of the survey objectives)
- Survey questions (between 3 and 8) questions. Each question has this format: question_text, schema.  The schema defines the structure for the question answers and can have the following values:
      ScaleSchema: this means Likert scale (1-5)
      OpenEndedSchema: for open-ended questions
      MultipleChoiceSchema: example: {Would you prefer a smartphone with fewer features at a lower price (A) or more features at a higher price (B) ? Answer with either A or B}
      YesNoSchema: for Yes/No answers
      RankingSchema: example: {Please rank the following features of a smartphone in terms of importance - from lowest to highest : Battery life, Display quality, Storage space, Durability}
You are free to decide on the apropriate number of questions and schema for each question.
If the user query is not compatible with your task you must always return the answer "Inadequate description!"
Provide the response in valid JSON format with fields: title, description, and questions array.'''


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




