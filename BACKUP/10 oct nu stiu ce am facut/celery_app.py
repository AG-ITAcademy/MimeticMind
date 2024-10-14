import multiprocessing
import logging
from celery import Celery
from config import Config

# Set multiprocessing to avoid Windows spawn issues
multiprocessing.set_start_method('spawn', force=True)

# Initialize Celery
celery = Celery(__name__)
celery.config_from_object(Config)

# Task routes
celery.conf.task_routes = {
    'profile.query_LLM': {'queue': 'celery'},
    'survey.process_survey_results': {'queue': 'celery'}  
}

# Correctly register tasks by using imports
celery.conf.update(
    imports=("profile", "survey")
)

celery.conf.result_extended = True  # Ensures result tracking for chord tasks
#celery.conf.task_annotations = {
#    'celery.chord_unlock': {'rate_limit': '10/m'},  # Ensures chord unlock task isn't failing
#}

# Set up logging manually
logger = logging.getLogger('celery')
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)

if __name__ == '__main__':
    logger.info("Starting Celery Worker")
