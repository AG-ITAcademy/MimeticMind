# report_generationbase.py

from abc import ABC, abstractmethod

class ReportSection(ABC):
    @abstractmethod
    def generate(self, analysis_results, context=None):
        pass
