import re
from typing import List, Dict, Set
from collections import Counter

class BiasDetector:
    def __init__(self):
        """Initialize bias detection with keyword dictionaries"""
        
        # Political bias keywords
        self.left_bias_words = {
            'progressive', 'liberal', 'social justice', 'equality', 'diversity', 'inclusive',
            'climate change', 'sustainable', 'renewable', 'tax the rich', 'medicare for all',
            'gun control', 'immigration reform', 'reproductive rights', 'pro-choice',
            'minimum wage', 'workers rights', 'union', 'regulation', 'big pharma',
            'corporate greed', 'wealth gap', 'systemic racism', 'defund'
        }
        
        self.right_bias_words = {
            'conservative', 'traditional values', 'family values', 'patriot', 'freedom',
            'liberty', 'free market', 'capitalism', 'small government', 'constitution',
            'second amendment', 'pro-life', 'border security', 'law and order',
            'american dream', 'individual responsibility', 'fiscal responsibility',
            'deregulation', 'job creators', 'socialist', 'communist', 'radical left',
            'mainstream media', 'fake news', 'deep state', 'swamp'
        }
        
        # Emotional manipulation words
        self.emotional_words = {
            'shocking', 'outrageous', 'disgusting', 'horrifying', 'devastating',
            'incredible', 'amazing', 'unbelievable', 'stunning', 'alarming',
            'terrifying', 'catastrophic', 'explosive', 'bombshell', 'scandalous',
            'unprecedented', 'historic', 'legendary', 'epic', 'mind-blowing',
            'heartbreaking', 'tragic', 'miraculous', 'extraordinary'
        }
        
        # Sensational language
        self.sensational_words = {
            'breaking', 'urgent', 'exclusive', 'revealed', 'exposed', 'uncovered',
            'secret', 'hidden', 'conspiracy', 'coverup', 'truth', 'reality',
            'everyone', 'nobody', 'always', 'never', 'completely', 'totally',
            'absolutely', 'definitely', 'undoubtedly', 'obviously', 'clearly',
            'proven', 'facts', 'evidence', 'study shows', 'experts say'
        }
        
        # Clickbait indicators
        self.clickbait_words = {
            'you won\'t believe', 'this will shock you', 'what happens next',
            'the reason will surprise you', 'doctors hate this', 'this one trick',
            'number 7 will amaze you', 'wait until you see', 'you need to see this',
            'this changes everything', 'gone wrong', 'gone viral', 'must see',
            'can\'t unsee', 'mind blown', 'game changer', 'life hack'
        }
        
        # Manipulative language patterns
        self.manipulative_patterns = [
            r'\b(don\'t let them|they don\'t want you|government hiding|media won\'t tell)\b',
            r'\b(wake up|open your eyes|the truth is|real truth|hidden agenda)\b',
            r'\b(them vs us|our people|real americans|true patriots)\b',
            r'\b(mainstream media|fake news|propaganda|brainwashed)\b',
            r'\b(crisis|emergency|urgent|immediate action|time is running out)\b'
        ]
        
        # Combine all bias words for general detection
        self.all_bias_words = (
            self.left_bias_words | 
            self.right_bias_words | 
            self.emotional_words | 
            self.sensational_words | 
            self.clickbait_words
        )

    def find_keyword_matches(self, text: str, word_set: Set[str]) -> List[str]:
        """Find matches for a specific set of keywords"""
        text_lower = text.lower()
        matches = []
        
        for word in word_set:
            # Use word boundaries for exact matches
            pattern = r'\b' + re.escape(word.lower()) + r'\b'
            if re.search(pattern, text_lower):
                matches.append(word)
        
        return matches

    def find_pattern_matches(self, text: str) -> List[str]:
        """Find matches for manipulative patterns"""
        matches = []
        text_lower = text.lower()
        
        for pattern in self.manipulative_patterns:
            pattern_matches = re.findall(pattern, text_lower, re.IGNORECASE)
            matches.extend(pattern_matches)
        
        return matches

    def calculate_bias_scores(self, text: str) -> Dict[str, float]:
        """Calculate bias scores for different categories"""
        word_count = len(text.split())
        
        if word_count == 0:
            return {
                'left_bias': 0.0,
                'right_bias': 0.0,
                'emotional': 0.0,
                'sensational': 0.0,
                'clickbait': 0.0
            }
        
        left_matches = len(self.find_keyword_matches(text, self.left_bias_words))
        right_matches = len(self.find_keyword_matches(text, self.right_bias_words))
        emotional_matches = len(self.find_keyword_matches(text, self.emotional_words))
        sensational_matches = len(self.find_keyword_matches(text, self.sensational_words))
        clickbait_matches = len(self.find_keyword_matches(text, self.clickbait_words))
        
        return {
            'left_bias': (left_matches / word_count) * 1000,  # Multiply by 1000 for readability
            'right_bias': (right_matches / word_count) * 1000,
            'emotional': (emotional_matches / word_count) * 1000,
            'sensational': (sensational_matches / word_count) * 1000,
            'clickbait': (clickbait_matches / word_count) * 1000
        }

    def determine_primary_bias(self, bias_scores: Dict[str, float]) -> str:
        """Determine the primary bias type based on scores"""
        # Thresholds for different bias types
        threshold = 2.0  # Minimum score to be considered biased
        
        max_score = max(bias_scores.values())
        if max_score < threshold:
            return 'Neutral'
        
        # Find the bias type with the highest score
        primary_bias = max(bias_scores.items(), key=lambda x: x[1])
        bias_type, score = primary_bias
        
        # Map internal names to display names
        bias_mapping = {
            'left_bias': 'Left',
            'right_bias': 'Right',
            'emotional': 'Emotional',
            'sensational': 'Sensational',
            'clickbait': 'Clickbait'
        }
        
        return bias_mapping.get(bias_type, 'Neutral')

    def extract_biased_words(self, text: str) -> List[str]:
        """Extract all biased words found in the text"""
        found_words = []
        
        # Find keyword matches
        for word_set_name, word_set in [
            ('political', self.left_bias_words | self.right_bias_words),
            ('emotional', self.emotional_words),
            ('sensational', self.sensational_words),
            ('clickbait', self.clickbait_words)
        ]:
            matches = self.find_keyword_matches(text, word_set)
            found_words.extend(matches)
        
        # Find pattern matches
        pattern_matches = self.find_pattern_matches(text)
        found_words.extend(pattern_matches)
        
        # Remove duplicates and sort
        unique_words = list(set(found_words))
        unique_words.sort()
        
        return unique_words

def find_biased_words(text: str) -> List[str]:
    """
    Main function to find biased words in text
    
    Args:
        text (str): The article text to analyze
        
    Returns:
        List[str]: List of biased/emotionally charged words found
    """
    if not text or len(text.strip()) < 10:
        return []
    
    detector = BiasDetector()
    biased_words = detector.extract_biased_words(text)
    
    # Limit to most relevant words (top 15)
    return biased_words[:15]

def analyze_bias_type(text: str) -> str:
    """
    Analyze text and return the primary bias type
    
    Args:
        text (str): The article text to analyze
        
    Returns:
        str: Primary bias type (Left, Right, Neutral, Emotional, Sensational, Clickbait)
    """
    if not text or len(text.strip()) < 10:
        return 'Neutral'
    
    detector = BiasDetector()
    bias_scores = detector.calculate_bias_scores(text)
    return detector.determine_primary_bias(bias_scores)

def get_bias_color(bias_type: str) -> str:
    """
    Get color code for bias type display
    
    Args:
        bias_type (str): The bias type
        
    Returns:
        str: Hex color code for the bias type
    """
    color_mapping = {
        'Left': '#2196F3',        # Blue
        'Right': '#F44336',       # Red
        'Neutral': '#4CAF50',     # Green
        'Emotional': '#FF9800',   # Orange
        'Sensational': '#9C27B0', # Purple
        'Clickbait': '#FF5722',   # Deep Orange
        'Unknown': '#607D8B'      # Blue Grey
    }
    
    return color_mapping.get(bias_type, '#607D8B')

def get_detailed_analysis(text: str) -> Dict:
    """
    Get detailed bias analysis including scores and breakdown
    
    Args:
        text (str): The article text to analyze
        
    Returns:
        Dict: Detailed analysis results
    """
    if not text or len(text.strip()) < 10:
        return {
            'biased_words': [],
            'primary_bias': 'Neutral',
            'bias_scores': {},
            'word_count': 0
        }
    
    detector = BiasDetector()
    
    biased_words = detector.extract_biased_words(text)
    bias_scores = detector.calculate_bias_scores(text)
    primary_bias = detector.determine_primary_bias(bias_scores)
    
    return {
        'biased_words': biased_words,
        'primary_bias': primary_bias,
        'bias_scores': bias_scores,
        'word_count': len(text.split())
    }

# Test function
def test_bias_detection():
    """Test function for development"""
    test_articles = [
        {
            'title': 'Neutral Article',
            'text': 'The city council met yesterday to discuss the annual budget. Members reviewed various proposals for infrastructure improvements and public services.'
        },
        {
            'title': 'Emotional/Sensational Article', 
            'text': 'BREAKING: This shocking discovery will absolutely blow your mind! Scientists have made an incredible breakthrough that changes everything we know. You won\'t believe what they found!'
        },
        {
            'title': 'Political Bias Article',
            'text': 'The progressive agenda continues to push radical socialist policies that threaten our traditional family values and constitutional freedoms.'
        }
    ]
    
    print("Testing bias detection...")
    
    for article in test_articles:
        print(f"\n--- {article['title']} ---")
        
        biased_words = find_biased_words(article['text'])
        bias_type = analyze_bias_type(article['text'])
        detailed = get_detailed_analysis(article['text'])
        
        print(f"Primary Bias: {bias_type}")
        print(f"Biased Words: {biased_words}")
        print(f"Bias Scores: {detailed['bias_scores']}")

if __name__ == "__main__":
    test_bias_detection()
