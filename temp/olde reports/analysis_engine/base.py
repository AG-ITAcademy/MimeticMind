# analysis_engine/base.py

from abc import ABC, abstractmethod

class AnalysisMethod(ABC):
    @abstractmethod
    def analyze(self, data):
        pass

    @abstractmethod
    def get_results(self):
        pass
