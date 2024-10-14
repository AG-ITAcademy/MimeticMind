# report_generation/introduction_section.py

from .base import ReportSection

class IntroductionSection(ReportSection):
    def generate(self, analysis_results, context):
        intro = f"Data Description: {context['data_description']}\n"
        intro += f"Methodology: {context['methodology']} This {context['description'].lower()}\n"
        return intro
