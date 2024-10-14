# analysis_engine/thematic_analysis.py

from .base import AnalysisMethod
import logging
from gensim import corpora
from gensim.models import LdaModel
from schemas.answer_schemas import schema_mapping
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import nltk

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ThematicAnalysis(AnalysisMethod):
    def __init__(self):
        self.results = {}
        #DON'T FORGET TO DOWNLOAD NTLK DATA AT FIRST RUN
        #nltk.download('punkt_tab')
        #nltk.download('stopwords')

    def analyze(self, data, schema):
        print('DATA: '+str(data))
        if schema not in schema_mapping:
            logger.warning(f"Schema {schema} not recognized.")
            return
        schema_class = schema_mapping[schema]
        field_name = list(schema_class.__fields__.keys())[0]
        texts = [item[field_name] for item in data if field_name in item]
        if not texts:
            logger.warning("No data available for thematic analysis.")
            self.results['thematic_analysis'] = "No data available."
            return
        stop_words = set(stopwords.words('english'))
        processed_texts = [
            [word.lower() for word in word_tokenize(text) if word.isalpha() and word.lower() not in stop_words]
            for text in texts
        ]
        dictionary = corpora.Dictionary(processed_texts)
        corpus = [dictionary.doc2bow(text) for text in processed_texts]
        if not dictionary.token2id:
            logger.warning("No valid tokens found for thematic analysis.")
            self.results['thematic_analysis'] = "No valid tokens found."
            return
        try:
            lda_model = LdaModel(corpus, num_topics=3, id2word=dictionary, passes=10)
            themes = lda_model.print_topics(num_words=5)
            self.results['thematic_analysis'] = themes
        except Exception as e:
            logger.error(f"Error during LDA modeling: {e}")
            self.results['thematic_analysis'] = "Error during thematic analysis."

    def get_results(self):
        return self.results
