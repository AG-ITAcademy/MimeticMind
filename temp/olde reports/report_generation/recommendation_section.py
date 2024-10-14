# report_generation/recommendation_section.py

from .base import ReportSection

class RecommendationSection(ReportSection):
    def generate(self, analysis_results, insights):
        recommendations = f"Based on the analysis, we recommend the following actions:\n"
        recommendations += insights
        return recommendations
