import os
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, List, Optional
from datetime import datetime
import json

class ArticleDatabase:
    def __init__(self):
        """Initialize database connection"""
        self.database_url = os.getenv("DATABASE_URL")
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable is not set")
    
    def get_connection(self):
        """Get a database connection"""
        return psycopg2.connect(self.database_url)
    
    def create_tables(self):
        """Create necessary database tables"""
        create_table_query = """
        CREATE TABLE IF NOT EXISTS article_analyses (
            id SERIAL PRIMARY KEY,
            url TEXT,
            title TEXT,
            verdict TEXT NOT NULL,
            confidence INTEGER NOT NULL,
            bias_type TEXT NOT NULL,
            explanation TEXT,
            biased_words JSONB,
            domain_score INTEGER,
            analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            article_hash TEXT
        );
        
        CREATE INDEX IF NOT EXISTS idx_url ON article_analyses(url);
        CREATE INDEX IF NOT EXISTS idx_analyzed_at ON article_analyses(analyzed_at DESC);
        CREATE INDEX IF NOT EXISTS idx_article_hash ON article_analyses(article_hash);
        """
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(create_table_query)
                    conn.commit()
            return True
        except Exception as e:
            print(f"Error creating tables: {e}")
            return False
    
    def save_analysis(self, 
                     url: Optional[str],
                     title: str,
                     verdict: str,
                     confidence: int,
                     bias_type: str,
                     explanation: str,
                     biased_words: List[str],
                     domain_score: Optional[int] = None,
                     article_hash: Optional[str] = None) -> bool:
        """Save an article analysis to the database"""
        
        insert_query = """
        INSERT INTO article_analyses 
        (url, title, verdict, confidence, bias_type, explanation, biased_words, domain_score, article_hash)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id;
        """
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(insert_query, (
                        url,
                        title,
                        verdict,
                        confidence,
                        bias_type,
                        explanation,
                        json.dumps(biased_words),
                        domain_score,
                        article_hash
                    ))
                    conn.commit()
            return True
        except Exception as e:
            print(f"Error saving analysis: {e}")
            return False
    
    def get_analyses_by_url(self, url: str) -> List[Dict]:
        """Get all analyses for a specific URL"""
        
        query = """
        SELECT id, url, title, verdict, confidence, bias_type, 
               explanation, biased_words, domain_score, analyzed_at
        FROM article_analyses
        WHERE url = %s
        ORDER BY analyzed_at DESC;
        """
        
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(query, (url,))
                    results = cur.fetchall()
                    
                    # Convert to list of dicts
                    analyses = []
                    for row in results:
                        analysis = dict(row)
                        # biased_words is already a list when retrieved from JSONB
                        if analysis.get('biased_words') and isinstance(analysis['biased_words'], str):
                            analysis['biased_words'] = json.loads(analysis['biased_words'])
                        analyses.append(analysis)
                    
                    return analyses
        except Exception as e:
            print(f"Error fetching analyses by URL: {e}")
            return []
    
    def get_recent_analyses(self, limit: int = 10) -> List[Dict]:
        """Get recent analyses"""
        
        query = """
        SELECT id, url, title, verdict, confidence, bias_type, 
               explanation, biased_words, domain_score, analyzed_at
        FROM article_analyses
        ORDER BY analyzed_at DESC
        LIMIT %s;
        """
        
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(query, (limit,))
                    results = cur.fetchall()
                    
                    # Convert to list of dicts
                    analyses = []
                    for row in results:
                        analysis = dict(row)
                        # biased_words is already a list when retrieved from JSONB
                        if analysis.get('biased_words') and isinstance(analysis['biased_words'], str):
                            analysis['biased_words'] = json.loads(analysis['biased_words'])
                        analyses.append(analysis)
                    
                    return analyses
        except Exception as e:
            print(f"Error fetching recent analyses: {e}")
            return []
    
    def get_analysis_statistics(self) -> Dict:
        """Get overall statistics from all analyses"""
        
        query = """
        SELECT 
            COUNT(*) as total_analyses,
            COUNT(DISTINCT url) as unique_urls,
            SUM(CASE WHEN verdict = 'FAKE' THEN 1 ELSE 0 END) as fake_count,
            SUM(CASE WHEN verdict = 'REAL' THEN 1 ELSE 0 END) as real_count,
            AVG(confidence) as avg_confidence,
            bias_type,
            COUNT(*) as bias_count
        FROM article_analyses
        GROUP BY bias_type;
        """
        
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # Get overall stats
                    cur.execute("""
                        SELECT 
                            COUNT(*) as total_analyses,
                            COUNT(DISTINCT url) as unique_urls,
                            SUM(CASE WHEN verdict = 'FAKE' THEN 1 ELSE 0 END) as fake_count,
                            SUM(CASE WHEN verdict = 'REAL' THEN 1 ELSE 0 END) as real_count,
                            AVG(confidence) as avg_confidence
                        FROM article_analyses;
                    """)
                    overall = dict(cur.fetchone())
                    
                    # Get bias type distribution
                    cur.execute("""
                        SELECT bias_type, COUNT(*) as count
                        FROM article_analyses
                        GROUP BY bias_type
                        ORDER BY count DESC;
                    """)
                    bias_distribution = [dict(row) for row in cur.fetchall()]
                    
                    overall['bias_distribution'] = bias_distribution
                    
                    return overall
        except Exception as e:
            print(f"Error fetching statistics: {e}")
            return {}

def init_database():
    """Initialize the database and create tables"""
    try:
        db = ArticleDatabase()
        db.create_tables()
        return db
    except Exception as e:
        print(f"Error initializing database: {e}")
        return None

# Test function
def test_database():
    """Test database operations"""
    db = init_database()
    if not db:
        print("Failed to initialize database")
        return
    
    print("Database initialized successfully!")
    
    # Test saving an analysis
    success = db.save_analysis(
        url="https://example.com/test-article",
        title="Test Article",
        verdict="FAKE",
        confidence=85,
        bias_type="Sensational",
        explanation="This is a test article with sensational language.",
        biased_words=["shocking", "breaking"],
        domain_score=50
    )
    
    if success:
        print("Test analysis saved successfully!")
    else:
        print("Failed to save test analysis")
    
    # Test retrieving analyses
    analyses = db.get_recent_analyses(5)
    print(f"Found {len(analyses)} recent analyses")
    
    # Test statistics
    stats = db.get_analysis_statistics()
    print(f"Statistics: {stats}")

if __name__ == "__main__":
    test_database()
