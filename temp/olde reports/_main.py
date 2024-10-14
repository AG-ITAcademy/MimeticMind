from orchestrator import AnalysisOrchestrator

if __name__ == "__main__":
    survey_id = 21  # Example survey ID
    orchestrator = AnalysisOrchestrator(survey_id)
    orchestrator.run()