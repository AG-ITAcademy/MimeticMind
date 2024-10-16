import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tag import pos_tag
from collections import Counter

nltk.download('vader_lexicon')
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('averaged_perceptron_tagger')
nltk.download('wordnet')

def perform_sentiment_analysis(responses):
    sia = SentimentIntensityAnalyzer()
    sentiments = {'Positive': 0, 'Neutral': 0, 'Negative': 0}
    
    for response in responses:
        sentiment_scores = sia.polarity_scores(response)
        compound_score = sentiment_scores['compound']
        
        if compound_score >= 0.05:
            sentiments['Positive'] += 1
        elif compound_score <= -0.05:
            sentiments['Negative'] += 1
        else:
            sentiments['Neutral'] += 1
    
    return [{'sentiment': k, 'count': v} for k, v in sentiments.items()]

def calculate_word_frequency(responses, top_n=30):
    stop_words = set(stopwords.words('english'))
    # Add custom stop words relevant to surveys
    custom_stop_words = {'survey', 'question', 'answer', 'think', 'feel', 'believe', 'opinion'}
    stop_words.update(custom_stop_words)
    
    lemmatizer = WordNetLemmatizer()
    words = []
    
    for response in responses:
        # Tokenize and lowercase
        tokens = word_tokenize(response.lower())
        
        # Filter and lemmatize words
        filtered_words = []
        for word in tokens:
            # Remove stop words, short words, and non-alphabetic words
            if word not in stop_words and len(word) > 2 and word.isalpha():
                # Lemmatize the word
                lemma = lemmatizer.lemmatize(word)
                filtered_words.append(lemma)
    
        words.extend(filtered_words)
    
    word_freq = Counter(words)
    top_words = word_freq.most_common(top_n)
    
    return [{'word': word, 'frequency': freq} for word, freq in top_words]