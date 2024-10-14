from sqlalchemy.orm import Session
from filter import Filter
from profile_model import ProfileModel
from profile import Profile
from template import SurveyTemplate, QueryTemplate, SurveyQueryParameter

class Survey:
    def __init__(self, filter_obj: Filter, session: Session, survey_template: SurveyTemplate, custom_parameters_dict: dict = None):
        self.filter = filter_obj
        self.session = session
        self.survey_template = survey_template
        self.custom_parameters_dict = custom_parameters_dict or {}  # Default to an empty dict if not provided

    def get_filtered_profiles(self):
        # Apply filters to the query to get profiles
        query = self.session.query(ProfileModel)
        query = self.filter.apply_filters(query)
        return query.all()

    def run_survey(self):
        # Retrieve profiles based on the filter criteria
        filtered_profiles = self.get_filtered_profiles()

        # Ensure the survey template is provided
        if not self.survey_template:
            return "Survey template not provided."

        # Ensure there are filtered profiles
        if not filtered_profiles:
            return "No profiles match the given criteria."

        # Call the method to survey profiles based on the query templates in the survey
        return self._survey_profiles(filtered_profiles)

    def _survey_profiles(self, filtered_profiles):
        """Private method to survey profiles using all query templates associated with the survey."""
        # Load all query templates associated with the survey
        query_templates = self.survey_template.query_templates

        if not query_templates:
            return "No query templates associated with the survey."

        # Survey each profile with all associated query templates
        for profile_model in filtered_profiles:
            profile = Profile.from_model(self.session, profile_model)  # Convert ProfileModel to Profile

            for query_template in query_templates:
                # Fetch default custom parameters for the current query template from the database
                db_custom_parameters = self.session.query(SurveyQueryParameter).filter_by(
                    survey_template_id=self.survey_template.id,
                    query_template_id=query_template.id
                ).all()

                # Replace placeholders with actual custom values, prioritizing user-provided values from custom_parameters_dict
                customized_query = query_template.description

                # First replace the placeholders with user-provided values (if any)
                for placeholder, value in self.custom_parameters_dict.items():
                    customized_query = customized_query.replace(f"[{placeholder}]", value)

                # Replace any remaining placeholders with values from the database
                for param in db_custom_parameters:
                    placeholder = f"[{param.parameter_name}]"
                    if placeholder in customized_query:  # Only replace if it hasn't been replaced by user input
                        customized_query = customized_query.replace(placeholder, param.parameter_value)

                print(f"\n\nquerying with: {customized_query}   SCHEMA: {query_template.schema}\n")

                # Using the customized query to generate responses
                answer = profile.answer_query(
                    session_id=1,
                    profile_id=profile_model.id,
                    query=customized_query,  # Using the customized query
                    template=query_template
                )

                # Print the profile ID, name, and the answer generated
                print(f"Profile ID: {profile_model.id}, Name: {profile_model.profile_name}")
                print(f"Generated Answer for query template '{query_template.name}': {answer}")

        # Return the number of profiles surveyed
        return f"{len(filtered_profiles)} profiles surveyed with {len(query_templates)} query templates."





