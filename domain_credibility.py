from urllib.parse import urlparse
from typing import Dict, Optional
import re

class DomainCredibility:
    def __init__(self):
        """Initialize domain credibility scorer with reputation database"""

        # High credibility sources (score 90-100)
        self.high_credibility = {
            'reuters.com', 'apnews.com', 'bbc.com', 'bbc.co.uk',
            'npr.org', 'pbs.org', 'propublica.org', 'reuters.co.uk',
            'theguardian.com', 'economist.com', 'wsj.com', 'ft.com',
            'nature.com', 'science.org', 'sciencemag.org', 'cell.com',
            'thelancet.com', 'nejm.org', 'who.int', 'cdc.gov',
            'gov.uk', 'usa.gov', 'europa.eu',
            # 🇮🇳 Indian High Credibility
            'thehindu.com', 'indianexpress.com', 'hindustantimes.com',
            'business-standard.com', 'livemint.com', 'ndtv.com',
            'scroll.in', 'theprint.in', 'moneycontrol.com',
            'newindianexpress.com'
        }

        # Good credibility sources (score 70-89)
        self.good_credibility = {
            'nytimes.com', 'washingtonpost.com', 'latimes.com',
            'usatoday.com', 'time.com', 'newsweek.com',
            'theatlantic.com', 'politico.com', 'axios.com',
            'bloomberg.com', 'cnbc.com', 'forbes.com',
            'techcrunch.com', 'wired.com', 'arstechnica.com',
            'scientificamerican.com', 'nationalgeographic.com',
            'smithsonianmag.com', 'history.com',
            # 🇮🇳 Indian Good Credibility
            'news18.com', 'indiatoday.in', 'dnaindia.com',
            'deccanherald.com', 'timesofindia.indiatimes.com',
            'firstpost.com', 'businessline.in', 'outlookindia.com',
            'theweek.in', 'republicworld.com'
        }

        # Moderate credibility sources (score 50-69)
        self.moderate_credibility = {
            'cnn.com', 'foxnews.com', 'msnbc.com', 'cbsnews.com',
            'abcnews.go.com', 'nbcnews.com', 'huffpost.com',
            'vice.com', 'buzzfeednews.com', 'vox.com',
            'slate.com', 'salon.com', 'dailybeast.com',
            'thehill.com', 'newsmax.com', 'thefederalist.com',
            'motherjones.com', 'jacobinmag.com', 'reason.com',
            # 🇮🇳 Indian Moderate Credibility
            'zee5.com', 'zeenews.india.com', 'wionews.com',
            'opindia.com', 'swarajyamag.com', 'oneindia.com',
            'freepressjournal.in', 'asianetnews.com', 'indiatvnews.com',
            'navbharattimes.indiatimes.com'
        }

        # Low credibility sources (score 20-49)
        self.low_credibility = {
            'breitbart.com', 'infowars.com', 'naturalnews.com',
            'beforeitsnews.com', 'yournewswire.com', 'neonnettle.com',
            'truthfeed.com', 'bigleaguepolitics.com', 'thegatewaypundit.com',
            'occupydemocrats.com', 'addictinginfo.com', 'palmerreport.com',
            'freedomdaily.com', 'conservativetribune.com', 'westernjournal.com',
            'politicususa.com', 'rawstory.com', 'alternet.org',
            # 🇮🇳 Indian Low Credibility
            'postcard.news', 'newsd.in', 'timesnownews.com',
            'punjabkesari.in', 'abplive.com', 'dailyo.in',
            'janmabhumi.in', 'tfipost.com', 'kreately.in', 'indiavoice.com'
        }

        # Known fake/satire sources (score 0-19)
        self.fake_satire = {
            'theonion.com', 'clickhole.com', 'babylonbee.com',
            'thebeaverton.com', 'privateeye.co.uk', 'newsthump.com',
            'worldnewsdailyreport.com', 'nationalreport.net',
            'empirenews.net', 'huzlers.com', 'reductress.com', 'thefauxy.com'
        }

        # Government and academic domain patterns (high credibility)
        self.trusted_tlds = {'.gov', '.edu', '.ac.uk', '.ac.in', '.nic.in'}

        # Suspicious patterns in domain names
        self.suspicious_patterns = [
            r'\d{2,}',  # Multiple consecutive numbers
            r'(-real|-true|-facts?|-news24|-breaking)',  # Suspicious keywords
            r'(fake|hoax|satire|parody)',  # Clear indicators
        ]

    def extract_domain(self, url: str) -> Optional[str]:
        """Extract clean domain from URL"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Remove www. prefix
            if domain.startswith('www.'):
                domain = domain[4:]
            
            # Remove subdomains for common news sites
            parts = domain.split('.')
            if len(parts) > 2:
                # Keep only main domain and TLD
                domain = '.'.join(parts[-2:])
            
            return domain
        except Exception as e:
            print(f"Error extracting domain: {e}")
            return None
    
    def check_suspicious_patterns(self, domain: str) -> bool:
        """Check if domain contains suspicious patterns"""
        for pattern in self.suspicious_patterns:
            if re.search(pattern, domain, re.IGNORECASE):
                return True
        return False
    
    def check_trusted_tld(self, domain: str) -> bool:
        """Check if domain has a trusted TLD"""
        for tld in self.trusted_tlds:
            if domain.endswith(tld):
                return True
        return False
    
    def calculate_domain_score(self, url: str) -> Dict:
        """
        Calculate credibility score for a domain
        
        Returns:
            Dict with 'score' (0-100), 'category', and 'explanation'
        """
        domain = self.extract_domain(url)
        
        if not domain:
            return {
                'score': 50,
                'category': 'Unknown',
                'explanation': 'Could not extract domain from URL'
            }
        
        # Check for satire/fake sources first
        if domain in self.fake_satire:
            return {
                'score': 10,
                'category': 'Satire/Fake',
                'explanation': f'{domain} is a known satire or fake news site'
            }
        
        # Check for suspicious patterns
        if self.check_suspicious_patterns(domain):
            return {
                'score': 25,
                'category': 'Suspicious',
                'explanation': f'{domain} contains suspicious patterns typical of unreliable sources'
            }
        
        # Check trusted TLDs (government, academic)
        if self.check_trusted_tld(domain):
            return {
                'score': 95,
                'category': 'Highly Trusted',
                'explanation': f'{domain} is a government or academic institution'
            }
        
        # Check reputation databases
        if domain in self.high_credibility:
            return {
                'score': 95,
                'category': 'Highly Credible',
                'explanation': f'{domain} is a well-established, highly credible news source'
            }
        
        if domain in self.good_credibility:
            return {
                'score': 80,
                'category': 'Good',
                'explanation': f'{domain} is a reputable news source with good credibility'
            }
        
        if domain in self.moderate_credibility:
            return {
                'score': 60,
                'category': 'Moderate',
                'explanation': f'{domain} has moderate credibility but may have some bias'
            }
        
        if domain in self.low_credibility:
            return {
                'score': 30,
                'category': 'Low Credibility',
                'explanation': f'{domain} is known for unreliable or heavily biased reporting'
            }
        
        # Unknown domain - neutral score
        return {
            'score': 50,
            'category': 'Unknown',
            'explanation': f'{domain} is not in our credibility database - exercise caution'
        }
    
    def get_score_color(self, score: int) -> str:
        """Get color code based on credibility score"""
        if score >= 80:
            return '#4CAF50'  # Green
        elif score >= 60:
            return '#8BC34A'  # Light Green
        elif score >= 40:
            return '#FF9800'  # Orange
        elif score >= 20:
            return '#F44336'  # Red
        else:
            return '#9C27B0'  # Purple (satire/fake)
    
    def get_recommendation(self, score: int) -> str:
        """Get recommendation based on score"""
        if score >= 80:
            return "✅ Generally trustworthy source"
        elif score >= 60:
            return "⚠️ Use caution and verify with other sources"
        elif score >= 40:
            return "⚠️ High risk of bias or misinformation"
        elif score >= 20:
            return "❌ Unreliable source - verify all claims"
        else:
            return "❌ Known fake/satire site - not credible"

def analyze_domain_credibility(url: str) -> Dict:
    """
    Main function to analyze domain credibility
    
    Args:
        url (str): The URL to analyze
        
    Returns:
        Dict: Credibility analysis with score, category, explanation, color, and recommendation
    """
    if not url:
        return {
            'score': None,
            'category': 'N/A',
            'explanation': 'No URL provided',
            'color': '#607D8B',
            'recommendation': 'Direct text input - no source URL to verify'
        }
    
    credibility = DomainCredibility()
    result = credibility.calculate_domain_score(url)
    result['color'] = credibility.get_score_color(result['score'])
    result['recommendation'] = credibility.get_recommendation(result['score'])
    result['domain'] = credibility.extract_domain(url)
    
    return result

# Test function
def test_domain_credibility():
    """Test domain credibility analysis"""
    test_urls = [
        "https://www.reuters.com/world/test-article",
        "https://www.nytimes.com/2024/test",
        "https://www.cnn.com/news/article",
        "https://www.infowars.com/fake-article",
        "https://www.theonion.com/satire-article",
        "https://www.cdc.gov/health/article",
        "https://unknown-news-site-2024.com/article"
    ]
    
    print("Testing Domain Credibility Analysis:\n")
    
    for url in test_urls:
        result = analyze_domain_credibility(url)
        print(f"URL: {url}")
        print(f"Domain: {result['domain']}")
        print(f"Score: {result['score']}/100 - {result['category']}")
        print(f"Explanation: {result['explanation']}")
        print(f"Recommendation: {result['recommendation']}")
        print("-" * 80)

if __name__ == "__main__":
    test_domain_credibility()
