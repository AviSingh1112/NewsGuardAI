import os
import json
import re
from groq import Groq
from typing import Dict, List, Optional

class GroqAnalyzer:
    def __init__(self):
        """Initialize the Groq client"""
        import os
        from groq import Groq

        # Try environment first
        self.api_key = os.getenv("GROQ_API_KEY")

        # Fallback: read directly from .env file if not loaded
        if not self.api_key and os.path.exists(".env"):
            with open(".env", "r") as f:
                for line in f:
                    if line.strip().startswith("GROQ_API_KEY="):
                        self.api_key = line.strip().split("=", 1)[1]
                        break

        if not self.api_key:
            raise ValueError(
                "❌ GROQ_API_KEY not found. Please ensure it is defined in your .env file like:\n"
                "GROQ_API_KEY=your_api_key_here"
            )

        try:
            self.client = Groq(api_key=self.api_key)
        except Exception as e:
            raise ValueError(f"Failed to initialize Groq client: {str(e)}")

        self.model_name = "llama-3.1-8b-instant"
    def create_analysis_prompt(self, article_text: str, biased_words: List[str]) -> str:
        """Create a comprehensive prompt for news analysis"""
        
        biased_words_str = ", ".join(biased_words) if biased_words else "None detected"
        
        prompt = f"""
You are an expert news analyst specializing in detecting fake news and media bias. Analyze the following news article and provide a comprehensive assessment.

ARTICLE TO ANALYZE:
{article_text[:4000]}  

BIASED WORDS ALREADY IDENTIFIED:
{biased_words_str}

Please analyze this article and respond with ONLY a valid JSON object in this exact format:
{{
    "verdict": "REAL" or "FAKE",
    "confidence": integer from 0-100,
    "bias_type": "Left", "Right", "Neutral", "Sensational", "Emotional", or "Clickbait",
    "explanation": "2-4 sentence explanation of your analysis focusing on credibility indicators, source reliability, factual accuracy, and bias detection"
}}

ANALYSIS CRITERIA:
1. CREDIBILITY ASSESSMENT:
   - Check for factual accuracy and verifiable claims
   - Look for proper sourcing and attribution
   - Assess logical consistency and reasoning
   - Identify sensationalism or exaggeration

2. BIAS DETECTION:
   - Left: Progressive/liberal political bias, supports social justice, big government, environmental regulations
   - Right: Conservative political bias, supports traditional values, free markets, limited government
   - Neutral: Balanced reporting with minimal political slant
   - Sensational: Exaggerated claims, dramatic language, designed to provoke strong reactions
   - Emotional: Appeals primarily to emotions rather than facts, manipulative language
   - Clickbait: Misleading headlines, withholding information to drive engagement

3. FAKE NEWS INDICATORS:
   - Completely fabricated stories or events
   - Manipulated quotes or false attributions
   - Misleading statistics or data
   - Conspiracy theories without evidence
   - Satirical content presented as real news

Provide your assessment as a JSON object only, no additional text.
"""
        return prompt

    def parse_analysis_response(self, response_text: str) -> Optional[Dict]:
        """Parse the JSON response from the AI model"""
        try:
            # Clean the response text
            response_text = response_text.strip()
            
            # Try to extract JSON from the response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                result = json.loads(json_str)
                
                # Validate required fields
                required_fields = ['verdict', 'confidence', 'bias_type', 'explanation']
                for field in required_fields:
                    if field not in result:
                        return None
                
                # Validate verdict
                if result['verdict'] not in ['REAL', 'FAKE']:
                    result['verdict'] = 'UNKNOWN'
                
                # Validate confidence (should be 0-100)
                try:
                    confidence = int(result['confidence'])
                    result['confidence'] = max(0, min(100, confidence))
                except:
                    result['confidence'] = 50
                
                # Validate bias_type
                valid_bias_types = ['Left', 'Right', 'Neutral', 'Sensational', 'Emotional', 'Clickbait']
                if result['bias_type'] not in valid_bias_types:
                    result['bias_type'] = 'Neutral'
                
                return result
            
            return None
            
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            return None
        except Exception as e:
            print(f"Response parsing error: {e}")
            return None

    def analyze_article(self, article_text: str, biased_words: List[str] = None) -> Dict:
        """Analyze an article using the Groq API"""
        if not article_text or len(article_text.strip()) < 50:
            return {
                'success': False,
                'error': 'Article text is too short for analysis',
                'result': None
            }
        
        if biased_words is None:
            biased_words = []
        
        try:
            # Create the analysis prompt
            prompt = self.create_analysis_prompt(article_text, biased_words)
            
            # Make API call to Groq
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert news analyst. Always respond with valid JSON only."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model=self.model_name,
                temperature=0.1,  # Low temperature for consistent analysis
                max_tokens=500,   # Limit response length
                top_p=0.9
            )
            
            # Extract the response
            response_content = chat_completion.choices[0].message.content
            
            # Parse the response
            parsed_result = self.parse_analysis_response(response_content)
            
            if parsed_result:
                return {
                    'success': True,
                    'error': '',
                    'result': parsed_result
                }
            else:
                # Fallback response if parsing fails
                return {
                    'success': True,
                    'error': '',
                    'result': {
                        'verdict': 'UNKNOWN',
                        'confidence': 50,
                        'bias_type': 'Neutral',
                        'explanation': 'Analysis completed but response format was unclear. The article requires manual review for definitive assessment.'
                    }
                }
                
        except Exception as e:
            error_msg = str(e)
            
            # Handle common API errors
            if "rate_limit" in error_msg.lower():
                error_msg = "Rate limit exceeded. Please wait a moment and try again."
            elif "api_key" in error_msg.lower() or "unauthorized" in error_msg.lower():
                error_msg = "API authentication failed. Please check your API key."
            elif "quota" in error_msg.lower():
                error_msg = "API quota exceeded. Please try again later."
            else:
                error_msg = f"Analysis failed: {error_msg}"
            
            return {
                'success': False,
                'error': error_msg,
                'result': None
            }

def analyze_article_with_groq(article_text: str, biased_words: List[str] = None) -> Dict:
    """
    Main function to analyze an article using Groq API
    
    Args:
        article_text (str): The news article content to analyze
        biased_words (List[str]): List of biased words found in the article
    
    Returns:
        Dict: Analysis result with success status, error message, and parsed result
    """
    try:
        analyzer = GroqAnalyzer()
        return analyzer.analyze_article(article_text, biased_words)
    
    except ValueError as e:
        return {
            'success': False,
            'error': str(e),
            'result': None
        }
    except Exception as e:
        return {
            'success': False,
            'error': f"Unexpected error initializing analyzer: {str(e)}",
            'result': None
        }

# Test function
def test_groq_analysis():
    """Test function for development"""
    test_article = """
    BREAKING: Scientists have discovered that drinking water can be dangerous! 
    New shocking research reveals that everyone who drinks water eventually dies. 
    The government doesn't want you to know this TRUTH! 
    This incredible discovery will change everything you thought you knew about hydration.
    """
    
    print("Testing Groq analysis...")
    result = analyze_article_with_groq(test_article, ["shocking", "TRUTH", "incredible"])
    
    if result['success']:
        print("✅ Analysis successful!")
        print(f"Result: {json.dumps(result['result'], indent=2)}")
    else:
        print(f"❌ Analysis failed: {result['error']}")

if __name__ == "__main__":
    test_groq_analysis()
