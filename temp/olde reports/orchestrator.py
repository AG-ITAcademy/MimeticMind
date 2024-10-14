# orchestrator.py

from data_access.data_access_layer import DataAccessLayer
from utils.helpers import get_analysis_methods_for_schema, create_context, interpret_results
from report_generation.introduction_section import IntroductionSection
from report_generation.graphical_section import GraphicalSection
from report_generation.recommendation_section import RecommendationSection

class AnalysisOrchestrator:
    def __init__(self, survey_id):
        self.survey_id = survey_id
        self.data_access = DataAccessLayer()
        self.analysis_plan = {}
        self.analysis_results = {}

    def run(self):
        self.load_data()
        self.select_analysis_methods()
        self.perform_analysis()
        report = self.generate_report()
        self.save_report(report)

    def load_data(self):
        self.data = self.data_access.get_survey_data(self.survey_id)
        print('DATA: '+str(self.data))
        if self.data is None:
            raise ValueError(f"No data found for survey ID: {self.survey_id}")
        print(f"Loaded survey data for Survey ID: {self.survey_id}")
    
    def select_analysis_methods(self):
        print("Selecting analysis methods based on answer schemas...")
        for question in self.data['questions']:
            question_id = question['question_id']
            schema = question['answer_schema']
            methods = get_analysis_methods_for_schema(schema)
            
            # Update the analysis_plan with both schema and methods
            self.analysis_plan[question_id] = {
                'schema': schema,
                'methods': methods
            }
            
            # Extract method names for display
            method_names = [method.__name__ for method in methods]
            print(f"Question ID {question_id} uses schema: {schema}, can apply methods: {method_names}")

    def perform_analysis(self):
        print("Performing analysis...")
        for question_id, details in self.analysis_plan.items():
            schema = details['schema']
            methods = details['methods']
            data = self.data_access.get_question_data(question_id)
            if data is None:
                print(f"No answers found for Question ID: {question_id}. Skipping analysis.")
                continue
            for method_class in methods:
                try:
                    method_instance = method_class()
                    method_instance.analyze(data, schema)
                    results = method_instance.get_results()
                    key = (question_id, method_class.__name__)
                    self.analysis_results[key] = results

                    #print(f"\nAnalysis Method: {method_class.__name__}")
                    print(f"Results for Question template ID {question_id}:")
                    print(results)
                except Exception as e:
                    print(f"Error performing {method_class.__name__} on Question template ID {question_id}: {e}")


    def generate_report(self):
        print("Generating report...")
        report = ""
        for (question_id, method_name), results in self.analysis_results.items():
            # Generate Introduction
            intro_section = IntroductionSection()
            context = create_context(question_id, method_name)
            intro = intro_section.generate(results, context)

            # Generate Graphical Section
            graph_section = GraphicalSection()
            graphs = graph_section.generate(results)

            # Generate Recommendations
            reco_section = RecommendationSection()
            insights = interpret_results(results)
            reco = reco_section.generate(results, insights)

            # Compile the report sections
            report += f"Question ID: {question_id}\n"
            report += f"Analysis Method: {method_name}\n"
            report += intro + "\n"
            report += graphs + "\n"
            report += reco + "\n\n"
        print("Report generation complete.")
        return report

    def save_report(self, report):
        report_filename = f"report_survey_{self.survey_id}.txt"
        try:
            with open(report_filename, "w") as f:
                f.write(report)
            print(f"Report successfully saved to {report_filename}")
        except Exception as e:
            print(f"Failed to save report: {e}")
