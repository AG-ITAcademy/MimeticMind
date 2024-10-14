# utils/helpers.py

from data_access.data_access_layer import DataAccessLayer
import importlib
import logging

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_analysis_methods_for_schema(schema_name):
    """
    Retrieves the analysis methods applicable for a given answer schema from the database.

    Args:
        schema_name (str): The name of the answer schema (e.g., 'ScaleSchema').

    Returns:
        list: A list of analysis method classes applicable for the schema.
    """
    dal = None  # Ensure dal is defined in the outer scope
    try:
        dal = DataAccessLayer()
        # Use the DataAccessLayer method to get analysis methods
        analysis_methods = dal.get_analysis_methods_for_schema(schema_name)
        analysis_method_classes = []

        for method in analysis_methods:
            module_name = method.module_name
            class_name = method.class_name
            method_class = import_analysis_method_class(module_name, class_name)
            if method_class:
                analysis_method_classes.append(method_class)
            else:
                logger.warning(f"Analysis method class '{class_name}' in module '{module_name}' not found.")

        return analysis_method_classes

    except Exception as e:
        logger.error(f"Error retrieving analysis methods for schema '{schema_name}': {e}")
        return []
    finally:
        if dal is not None:
            dal.close_connection()

def import_analysis_method_class(module_name, class_name):
    """
    Dynamically imports an analysis method class from the given module.

    Args:
        module_name (str): The name of the module where the class is defined.
        class_name (str): The name of the class to import.

    Returns:
        class: The imported class, or None if not found.
    """
    try:
        module = importlib.import_module(f'analysis_engine.{module_name}')
        method_class = getattr(module, class_name)
        return method_class
    except (ImportError, AttributeError) as e:
        logger.error(f"Error importing class '{class_name}' from module '{module_name}': {e}")
        return None

def create_context(question_id, method_class_name):
    """
    Creates context information for the report by fetching details from the database.

    Args:
        question_id (int): The ID of the question.
        method_name (str): The name of the analysis method.

    Returns:
        dict: A dictionary containing data description, methodology, and conventions.
    """
    dal = None  # Ensure dal is defined in the outer scope
    try:
        dal = DataAccessLayer()
        # Fetch question text
        question = dal.get_question_template(question_id)
        question_text = question.query_text if question else "Unknown Question"

        # Fetch method description
        analysis_method = dal.get_analysis_method_by_name(method_class_name)
        #print("ANALYSIS METHOD:" & str(analysis_method))
        method_description = analysis_method.description if analysis_method else "Method description not found."

        context = {
            'data_description': f"The data consists of responses to the question: '{question_text}'.",
            'methodology': f"We applied {method_class_name} to analyze the data.",
            'description': method_description
        }
        #print(context)
        return context
    except Exception as e:
        logger.error(f"Error creating context for question ID '{question_id}' and method '{method_name}': {e}")
        return {}
    finally:
        if dal is not None:
            dal.close_connection()

def interpret_results(results):
    """
    Provides interpretations based on analysis results.

    Args:
        results (dict): The results from the analysis.

    Returns:
        str: Interpretation and insights based on the results.
    """
    # Implement logic to interpret the results
    # This could be a rule-based system or utilize machine learning models
    return "Interpretation and insights based on the results."
