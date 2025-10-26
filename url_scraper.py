import requests
from bs4 import BeautifulSoup
import trafilatura
import re
from urllib.parse import urlparse
from newspaper import Article
from playwright.sync_api import sync_playwright


class ArticleScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def is_valid_url(self, url):
        """Check if the URL is valid"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False

    def clean_text(self, text):
        """Clean extracted text"""
        if not text:
            return ""
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r' +', ' ', text)
        return text.strip()

    def extract_metadata(self, soup, url):
        """Extract article metadata"""
        metadata = {'title': '', 'author': '', 'date': '', 'description': ''}
        try:
            title_tag = soup.find('title')
            if title_tag:
                metadata['title'] = title_tag.get_text().strip()

            meta_title = soup.find('meta', property='og:title') or soup.find('meta', attrs={'name': 'title'})
            if meta_title and meta_title.get('content'):
                metadata['title'] = meta_title['content'].strip()

            h1_tag = soup.find('h1')
            if h1_tag and not metadata['title']:
                metadata['title'] = h1_tag.get_text().strip()

            author_elem = soup.find('meta', attrs={'name': 'author'})
            if author_elem and author_elem.get('content'):
                metadata['author'] = author_elem['content'].strip()

            date_elem = soup.find('meta', property='article:published_time')
            if date_elem and date_elem.get('content'):
                metadata['date'] = date_elem['content'].strip()

            desc_elem = soup.find('meta', property='og:description') or soup.find('meta', attrs={'name': 'description'})
            if desc_elem and desc_elem.get('content'):
                metadata['description'] = desc_elem['content'].strip()

        except Exception as e:
            print(f"[Metadata Error] {e}")
        return metadata

    def scrape_with_trafilatura(self, url):
        try:
            print("🔍 Trying Trafilatura...")
            downloaded = trafilatura.fetch_url(url)
            if not downloaded:
                return None
            text = trafilatura.extract(downloaded)
            if not text:
                return None
            metadata = trafilatura.extract_metadata(downloaded)
            return {
                'content': self.clean_text(text),
                'title': getattr(metadata, 'title', ''),
                'author': getattr(metadata, 'author', ''),
                'date': getattr(metadata, 'date', ''),
                'description': getattr(metadata, 'description', '')
            }
        except Exception as e:
            print(f"[Trafilatura Error] {e}")
            return None

    def scrape_with_beautifulsoup(self, url):
        try:
            print("🧠 Trying BeautifulSoup...")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'lxml')
            metadata = self.extract_metadata(soup, url)
            paragraphs = [p.get_text() for p in soup.find_all('p')]
            content = self.clean_text("\n".join(paragraphs))
            metadata['content'] = content
            return metadata if content else None
        except Exception as e:
            print(f"[BeautifulSoup Error] {e}")
            return None

    def scrape_with_newspaper(self, url):
        try:
            print("📰 Trying Newspaper3k...")
            article = Article(url)
            article.download()
            article.parse()
            return {
                'content': self.clean_text(article.text),
                'title': article.title or '',
                'author': ', '.join(article.authors) if article.authors else '',
                'date': str(article.publish_date) if article.publish_date else '',
                'description': article.meta_description or ''
            }
        except Exception as e:
            print(f"[Newspaper3k Error] {e}")
            return None

    def scrape_with_playwright(self, url):
        try:
            print("🎭 Trying Playwright (JS rendering)...")
            with sync_playwright() as p:
                browser = p.firefox.launch(headless=True)
                page = browser.new_page()
                page.goto(url, timeout=40000)
                html = page.content()
                browser.close()
            soup = BeautifulSoup(html, "lxml")
            paragraphs = [p.get_text() for p in soup.find_all("p")]
            text = "\n".join(paragraphs)
            return {'content': self.clean_text(text)} if text else None
        except Exception as e:
            print(f"[Playwright Error] {e}")
            return None


def extract_article_content(url):
    scraper = ArticleScraper()

    if not scraper.is_valid_url(url):
        return {'success': False, 'error': 'Invalid URL format', 'content': ''}

    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    result = None

    # Try each extractor in sequence, stop when one works
    for method in [
        scraper.scrape_with_trafilatura,
        scraper.scrape_with_beautifulsoup,
        scraper.scrape_with_newspaper,
        scraper.scrape_with_playwright
    ]:
        result = method(url)
        if result and len(result.get('content', '')) > 50:
            print(f"✅ Extracted successfully using {method.__name__}")
            break

    if not result or len(result.get('content', '')) < 20:
        return {
            'success': False,
            'error': 'Unable to extract readable content. The site may use paywalls or advanced JS.',
            'content': ''
        }

    return {
        'success': True,
        'error': '',
        'content': result.get('content', ''),
        'title': result.get('title', ''),
        'author': result.get('author', ''),
        'date': result.get('date', ''),
        'description': result.get('description', '')
    }


# Test block
if __name__ == "__main__":
    urls = [
        "https://www.thehindu.com/news/national/india-to-host-g20-summit-in-september/article67148429.ece",
        "https://www.indiatoday.in/india/story/lok-sabha-elections-2024-results-live-updates-bjp-congress-ndtv-news-2521781-2024-06-04",
        "https://www.ndtv.com/india-news/supreme-court-orders-release-of-all-detention-centre-inmates-in-assam-5410243",
        "https://thefauxy.com/indian-govt-introduces-degree-in-whatsapp-university/"
    ]

    for url in urls:
        print(f"\n🔗 Testing: {url}")
        result = extract_article_content(url)
        if result["success"]:
            print(f"✅ Success | Title: {result.get('title', '')}")
            print(f"📝 Length: {len(result['content'])} chars\n")
        else:
            print(f"❌ Failed | {result['error']}\n")
