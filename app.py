import streamlit as st
import time
import json
import hashlib
from url_scraper import extract_article_content
from groq_api import analyze_article_with_groq
from bias_keywords import find_biased_words, get_bias_color
from database import init_database
from domain_credibility import analyze_domain_credibility
from export_reports import generate_json_report, generate_pdf_report

# Page configuration
st.set_page_config(
    page_title="AI-Powered Fake News & Bias Detector",
    page_icon="🔍",
    layout="wide"
)

# Initialize session state
if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = None
if 'article_text' not in st.session_state:
    st.session_state.article_text = ""
if 'input_key' not in st.session_state:
    st.session_state.input_key = 0
if 'current_url' not in st.session_state:
    st.session_state.current_url = None
if 'article_title' not in st.session_state:
    st.session_state.article_title = ""
if 'domain_credibility' not in st.session_state:
    st.session_state.domain_credibility = None
if 'db' not in st.session_state:
    st.session_state.db = init_database()
if 'comparison_mode' not in st.session_state:
    st.session_state.comparison_mode = False
if 'comparison_articles' not in st.session_state:
    st.session_state.comparison_articles = []

def generate_article_hash(text):
    """Generate a hash for the article text to track unique articles"""
    return hashlib.md5(text.encode()).hexdigest()

def highlight_biased_words(text, biased_words):
    """Highlight biased words in the text"""
    if not biased_words:
        return text
    
    highlighted_text = text
    for word in biased_words:
        # Case-insensitive replacement with HTML highlighting
        import re
        pattern = re.compile(re.escape(word), re.IGNORECASE)
        highlighted_text = pattern.sub(f'<mark style="background-color: #ffeb3b;">{word}</mark>', highlighted_text)
    
    return highlighted_text

def display_analysis_results(result):
    """Display the analysis results in a formatted way"""
    if not result:
        return
    
    # Main verdict with color coding
    verdict = result.get('verdict', 'Unknown').upper()
    confidence = result.get('confidence', 0)
    
    # Color coding for verdict
    if verdict == 'REAL':
        verdict_color = "#4CAF50"  # Green
    elif verdict == 'FAKE':
        verdict_color = "#F44336"  # Red
    else:
        verdict_color = "#FF9800"  # Orange
    
    # Display verdict
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown(f"""
        <div style="padding: 20px; border-radius: 10px; background-color: {verdict_color}; color: white; text-align: center;">
            <h2 style="margin: 0; color: white;">Verdict: {verdict}</h2>
            <p style="margin: 5px 0; color: white;">Confidence: {confidence}%</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # Bias detection
        bias_type = result.get('bias_type', 'Unknown')
        bias_color = get_bias_color(bias_type)
        
        st.markdown(f"""
        <div style="padding: 20px; border-radius: 10px; background-color: {bias_color}; color: white; text-align: center;">
            <h3 style="margin: 0; color: white;">Bias Type</h3>
            <p style="margin: 5px 0; color: white; font-size: 18px;">{bias_type}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Progress bar for confidence
    st.subheader("Confidence Level")
    st.progress(confidence / 100)
    
    # Explanation
    st.subheader("Analysis Explanation")
    explanation = result.get('explanation', 'No explanation provided.')
    st.write(explanation)
    
    # Domain credibility section (if URL was provided)
    if st.session_state.domain_credibility and st.session_state.domain_credibility.get('score') is not None:
        st.subheader("🌐 Source Credibility")
        
        domain_cred = st.session_state.domain_credibility
        domain_score = domain_cred['score']
        domain_color = domain_cred['color']
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown(f"""
            <div style="padding: 15px; border-radius: 10px; background-color: {domain_color}; color: white; text-align: center;">
                <h3 style="margin: 0; color: white;">Domain Score</h3>
                <h1 style="margin: 5px 0; color: white;">{domain_score}/100</h1>
                <p style="margin: 0; color: white; font-size: 14px;">{domain_cred['category']}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.write(f"**Domain:** {domain_cred.get('domain', 'N/A')}")
            st.write(f"**Assessment:** {domain_cred['explanation']}")
            st.write(f"**Recommendation:** {domain_cred['recommendation']}")
        
        st.progress(domain_score / 100)
    
    # Biased words section
    biased_words = result.get('biased_words', [])
    if biased_words:
        st.subheader("Identified Biased/Emotionally Charged Words")
        
        # Display biased words as badges
        badge_html = ""
        for word in biased_words:
            badge_html += f'<span style="background-color: #ffeb3b; color: #000; padding: 5px 10px; margin: 2px; border-radius: 15px; font-size: 12px;">{word}</span> '
        
        st.markdown(badge_html, unsafe_allow_html=True)
        
        # Show highlighted text
        st.subheader("Article with Highlighted Biased Words")
        highlighted_text = highlight_biased_words(st.session_state.article_text, biased_words)
        st.markdown(highlighted_text, unsafe_allow_html=True)

def main():
    # Title and description
    st.title("🔍 AI-Powered Fake News & Bias Detector")
    st.markdown("**Powered by Groq's Llama 3.1 8B Instant Model**")
    st.markdown("Analyze news articles for authenticity and bias using advanced AI. Enter text directly or provide a URL.")
    
    # Mode selection
    mode = st.radio(
        "Select Mode:",
        ["🔍 Single Article Analysis", "⚖️ Compare Multiple Articles"],
        horizontal=True
    )
    
    if mode == "⚖️ Compare Multiple Articles":
        # Comparison mode
        st.markdown("---")
        st.subheader("Compare Multiple Articles Side-by-Side")
        st.write("Analyze and compare 2-4 articles to see differences in credibility, bias, and authenticity.")
        
        num_articles = st.slider("Number of articles to compare:", 2, 4, 2)
        
        comparison_data = []
        
        for i in range(num_articles):
            st.markdown(f"### Article {i+1}")
            
            col1, col2 = st.columns([1, 3])
            
            with col1:
                input_type = st.radio(
                    f"Input type for Article {i+1}:",
                    ["Text", "URL"],
                    key=f"input_type_{i}"
                )
            
            with col2:
                if input_type == "URL":
                    article_url = st.text_input(
                        f"Enter URL for Article {i+1}:",
                        key=f"url_{i}",
                        placeholder="https://example.com/article"
                    )
                    
                    if article_url:
                        comparison_data.append({
                            'type': 'url',
                            'url': article_url,
                            'text': None
                        })
                else:
                    article_text = st.text_area(
                        f"Paste text for Article {i+1}:",
                        key=f"text_{i}",
                        height=150,
                        placeholder="Paste article text here..."
                    )
                    
                    if article_text:
                        comparison_data.append({
                            'type': 'text',
                            'url': None,
                            'text': article_text
                        })
        
        # Analyze comparison button
        if st.button("🔍 Analyze & Compare All Articles", type="primary"):
            if len(comparison_data) < 2:
                st.error("Please provide at least 2 articles to compare.")
            else:
                results = []
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for idx, article_data in enumerate(comparison_data):
                    status_text.text(f"Analyzing Article {idx+1}/{len(comparison_data)}...")
                    progress_bar.progress((idx) / len(comparison_data))
                    
                    try:
                        # Extract article if URL
                        if article_data['type'] == 'url':
                            extraction = extract_article_content(article_data['url'])
                            if not extraction['success']:
                                st.warning(f"Failed to extract Article {idx+1}: {extraction['error']}")
                                continue
                            
                            article_text = extraction['content']
                            article_title = extraction['title']
                            article_url = article_data['url']
                            domain_cred = analyze_domain_credibility(article_url)
                        else:
                            article_text = article_data['text']
                            article_title = f"Article {idx+1}"
                            article_url = None
                            domain_cred = None
                        
                        # Analyze with Groq
                        biased_words = find_biased_words(article_text)
                        analysis = analyze_article_with_groq(article_text, biased_words)
                        
                        if analysis['success']:
                            result = analysis['result']
                            result['biased_words'] = biased_words
                            result['title'] = article_title
                            result['url'] = article_url
                            result['domain_credibility'] = domain_cred
                            results.append(result)
                        
                    except Exception as e:
                        st.warning(f"Error analyzing Article {idx+1}: {str(e)}")
                
                progress_bar.progress(1.0)
                status_text.text("✅ Analysis complete!")
                time.sleep(0.5)
                progress_bar.empty()
                status_text.empty()
                
                # Display comparison results
                if len(results) >= 2:
                    st.markdown("---")
                    st.header("📊 Comparison Results")
                    
                    # Create comparison table
                    comparison_table_data = []
                    headers = ["Metric"] + [f"Article {i+1}" for i in range(len(results))]
                    
                    # Titles
                    title_row = ["Title"]
                    for r in results:
                        title_row.append(r['title'][:40] + "..." if len(r['title']) > 40 else r['title'])
                    comparison_table_data.append(title_row)
                    
                    # Verdicts
                    verdict_row = ["Verdict"]
                    for r in results:
                        verdict_row.append(r['verdict'])
                    comparison_table_data.append(verdict_row)
                    
                    # Confidence
                    confidence_row = ["Confidence"]
                    for r in results:
                        confidence_row.append(f"{r['confidence']}%")
                    comparison_table_data.append(confidence_row)
                    
                    # Bias Type
                    bias_row = ["Bias Type"]
                    for r in results:
                        bias_row.append(r['bias_type'])
                    comparison_table_data.append(bias_row)
                    
                    # Domain Score
                    if any(r.get('domain_credibility') for r in results):
                        domain_row = ["Domain Score"]
                        for r in results:
                            if r.get('domain_credibility') and r['domain_credibility'].get('score') is not None:
                                domain_row.append(f"{r['domain_credibility']['score']}/100")
                            else:
                                domain_row.append("N/A")
                        comparison_table_data.append(domain_row)
                    
                    # Display as table
                    import pandas as pd
                    df = pd.DataFrame(comparison_table_data[1:], columns=comparison_table_data[0])
                    st.table(df)
                    
                    # Detailed results for each article
                    st.markdown("---")
                    st.subheader("Detailed Analysis for Each Article")
                    
                    for idx, result in enumerate(results):
                        with st.expander(f"📄 Article {idx+1}: {result['title']}"):
                            col1, col2, col3 = st.columns(3)
                            
                            verdict_color = "#4CAF50" if result['verdict'] == 'REAL' else "#F44336" if result['verdict'] == 'FAKE' else "#FF9800"
                            
                            with col1:
                                st.markdown(f"""
                                <div style="padding: 15px; border-radius: 10px; background-color: {verdict_color}; color: white; text-align: center;">
                                    <h3 style="margin: 0; color: white;">{result['verdict']}</h3>
                                    <p style="margin: 0; color: white;">{result['confidence']}%</p>
                                </div>
                                """, unsafe_allow_html=True)
                            
                            with col2:
                                bias_color = get_bias_color(result['bias_type'])
                                st.markdown(f"""
                                <div style="padding: 15px; border-radius: 10px; background-color: {bias_color}; color: white; text-align: center;">
                                    <h3 style="margin: 0; color: white;">{result['bias_type']}</h3>
                                    <p style="margin: 0; color: white;">Bias</p>
                                </div>
                                """, unsafe_allow_html=True)
                            
                            with col3:
                                if result.get('domain_credibility') and result['domain_credibility'].get('score') is not None:
                                    domain_score = result['domain_credibility']['score']
                                    domain_color = result['domain_credibility']['color']
                                    st.markdown(f"""
                                    <div style="padding: 15px; border-radius: 10px; background-color: {domain_color}; color: white; text-align: center;">
                                        <h3 style="margin: 0; color: white;">{domain_score}/100</h3>
                                        <p style="margin: 0; color: white;">Domain</p>
                                    </div>
                                    """, unsafe_allow_html=True)
                            
                            st.write(f"**Explanation:** {result['explanation']}")
                            
                            if result.get('biased_words'):
                                badge_html = "**Biased Words:** "
                                for word in result['biased_words'][:10]:
                                    badge_html += f'<span style="background-color: #ffeb3b; color: #000; padding: 3px 8px; margin: 2px; border-radius: 10px; font-size: 11px;">{word}</span> '
                                st.markdown(badge_html, unsafe_allow_html=True)
                
                else:
                    st.error("Not enough articles were successfully analyzed for comparison.")
        
        return  # Exit early if in comparison mode
    
    # Single article analysis mode (existing code)
    # Input method selection
    input_method = st.radio(
        "Choose input method:",
        ["📝 Paste Article Text", "🔗 Enter URL"],
        horizontal=True
    )
    
    article_text = ""
    
    if input_method == "📝 Paste Article Text":
        article_text = st.text_area(
            "Paste your news article here:",
            value=st.session_state.article_text,
            height=200,
            placeholder="Paste the full news article text here...",
            key=f"article_input_{st.session_state.input_key}"
        )
    
    else:  # URL input
        url = st.text_input(
            "Enter news article URL:",
            placeholder="https://example.com/news-article"
        )
        
        if url and st.button("🔍 Extract Article"):
            with st.spinner("Extracting article content..."):
                try:
                    extraction_result = extract_article_content(url)
                    if extraction_result['success']:
                        article_text = extraction_result['content']
                        st.session_state.current_url = url
                        st.session_state.article_title = extraction_result['title']
                        
                        # Calculate domain credibility
                        st.session_state.domain_credibility = analyze_domain_credibility(url)
                        
                        st.success(f"✅ Successfully extracted article: {extraction_result['title']}")
                        
                        # Show metadata
                        with st.expander("📋 Article Metadata"):
                            st.write(f"**Title:** {extraction_result['title']}")
                            st.write(f"**Author:** {extraction_result['author']}")
                            st.write(f"**Publication Date:** {extraction_result['date']}")
                            st.write(f"**Word Count:** {len(article_text.split())} words")
                        
                        # Show extracted text
                        st.text_area(
                            "Extracted Article Text:",
                            value=article_text,
                            height=200,
                            disabled=True
                        )
                    else:
                        st.error(f"❌ Failed to extract article: {extraction_result['error']}")
                        return
                
                except Exception as e:
                    st.error(f"❌ Error extracting article: {str(e)}")
                    return
    
    # Store article text in session state
    if article_text:
        st.session_state.article_text = article_text
    
    # Analyze button
    if st.session_state.article_text and st.button("🤖 Analyze Article", type="primary"):
        if len(st.session_state.article_text.strip()) < 50:
            st.error("❌ Please provide a longer article (at least 50 characters) for accurate analysis.")
            return
        
        # Create progress indicators
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Step 1: Find biased words
            status_text.text("🔍 Identifying biased words...")
            progress_bar.progress(25)
            time.sleep(0.5)
            
            biased_words = find_biased_words(st.session_state.article_text)
            
            # Step 2: Analyze with Groq
            status_text.text("🤖 Analyzing with AI model...")
            progress_bar.progress(50)
            
            analysis_result = analyze_article_with_groq(st.session_state.article_text, biased_words)
            
            if not analysis_result['success']:
                st.error(f"❌ Analysis failed: {analysis_result['error']}")
                return
            
            progress_bar.progress(75)
            status_text.text("📊 Processing results...")
            time.sleep(0.5)
            
            # Combine results
            final_result = analysis_result['result']
            final_result['biased_words'] = biased_words
            
            progress_bar.progress(100)
            status_text.text("✅ Analysis complete!")
            time.sleep(0.5)
            
            # Clear progress indicators
            progress_bar.empty()
            status_text.empty()
            
            # Store results
            st.session_state.analysis_result = final_result
            
            # Save to database if database is initialized
            if st.session_state.db:
                try:
                    article_hash = generate_article_hash(st.session_state.article_text)
                    domain_score = None
                    if st.session_state.domain_credibility:
                        domain_score = st.session_state.domain_credibility.get('score')
                    
                    st.session_state.db.save_analysis(
                        url=st.session_state.current_url,
                        title=st.session_state.article_title or "Pasted Article",
                        verdict=final_result['verdict'],
                        confidence=final_result['confidence'],
                        bias_type=final_result['bias_type'],
                        explanation=final_result['explanation'],
                        biased_words=biased_words,
                        domain_score=domain_score,
                        article_hash=article_hash
                    )
                except Exception as db_error:
                    print(f"Database save failed: {db_error}")
            
        except Exception as e:
            st.error(f"❌ An error occurred during analysis: {str(e)}")
            progress_bar.empty()
            status_text.empty()
    
    # Display results if available
    if st.session_state.analysis_result:
        st.markdown("---")
        st.header("📊 Analysis Results")
        display_analysis_results(st.session_state.analysis_result)
        
        # Export buttons
        st.markdown("---")
        st.subheader("📥 Export Analysis Report")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # JSON Export
            json_report = generate_json_report(
                st.session_state.analysis_result,
                st.session_state.article_text,
                st.session_state.current_url,
                st.session_state.domain_credibility
            )
            
            st.download_button(
                label="📄 Download JSON Report",
                data=json_report,
                file_name=f"analysis_report_{int(time.time())}.json",
                mime="application/json",
                use_container_width=True
            )
        
        with col2:
            # PDF Export
            pdf_buffer = generate_pdf_report(
                st.session_state.analysis_result,
                st.session_state.article_text,
                st.session_state.current_url,
                st.session_state.article_title,
                st.session_state.domain_credibility
            )
            
            st.download_button(
                label="📑 Download PDF Report",
                data=pdf_buffer.getvalue(),
                file_name=f"analysis_report_{int(time.time())}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
    
    # Historical Analysis Section (after results)
    if st.session_state.db:
        st.markdown("---")
        st.header("📊 Historical Analysis")
        
        tab1, tab2 = st.tabs(["Recent Analyses", "Statistics"])
        
        with tab1:
            # Get recent analyses
            recent_analyses = st.session_state.db.get_recent_analyses(limit=10)
            
            if recent_analyses:
                st.subheader("Recent Article Analyses")
                
                for analysis in recent_analyses:
                    verdict_emoji = "✅" if analysis['verdict'] == 'REAL' else "❌" if analysis['verdict'] == 'FAKE' else "❓"
                    
                    with st.expander(f"{verdict_emoji} {analysis['title'][:60]}... ({analysis['analyzed_at'].strftime('%Y-%m-%d %H:%M')})"):
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("Verdict", analysis['verdict'])
                        with col2:
                            st.metric("Confidence", f"{analysis['confidence']}%")
                        with col3:
                            st.metric("Bias", analysis['bias_type'])
                        
                        if analysis.get('url'):
                            st.write(f"**URL:** {analysis['url'][:80]}...")
                        
                        if analysis.get('domain_score'):
                            st.write(f"**Domain Score:** {analysis['domain_score']}/100")
                        
                        st.write(f"**Explanation:** {analysis['explanation'][:200]}...")
                        
                        if analysis.get('biased_words'):
                            badge_html = "**Biased Words:** "
                            for word in analysis['biased_words'][:8]:
                                badge_html += f'<span style="background-color: #ffeb3b; color: #000; padding: 3px 8px; margin: 2px; border-radius: 10px; font-size: 11px;">{word}</span> '
                            st.markdown(badge_html, unsafe_allow_html=True)
            else:
                st.info("No analyses yet. Start by analyzing your first article!")
        
        with tab2:
            # Get statistics
            stats = st.session_state.db.get_analysis_statistics()
            
            if stats and stats.get('total_analyses', 0) > 0:
                st.subheader("Overall Statistics")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Analyses", stats.get('total_analyses', 0))
                with col2:
                    st.metric("Unique URLs", stats.get('unique_urls', 0))
                with col3:
                    st.metric("Fake Articles", stats.get('fake_count', 0))
                with col4:
                    st.metric("Real Articles", stats.get('real_count', 0))
                
                # Average confidence
                avg_conf = stats.get('avg_confidence', 0)
                if avg_conf:
                    st.metric("Average Confidence", f"{float(avg_conf):.1f}%")
                
                # Bias distribution
                if stats.get('bias_distribution'):
                    st.subheader("Bias Type Distribution")
                    
                    bias_data = stats['bias_distribution']
                    for bias_item in bias_data:
                        bias_type = bias_item['bias_type']
                        count = bias_item['count']
                        percentage = (count / stats['total_analyses']) * 100
                        
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.progress(percentage / 100, text=f"{bias_type}: {count} articles ({percentage:.1f}%)")
                        with col2:
                            st.write(f"{count}")
            else:
                st.info("No statistics available yet. Analyze some articles to see trends!")
    
    # Sidebar with information
    with st.sidebar:
        st.header("ℹ️ About")
        st.markdown("""
        This AI-powered tool helps you:
        
        • **Detect Fake News** - Determines if an article is likely fake or real
        • **Identify Bias** - Spots political, emotional, or sensational bias
        • **Highlight Keywords** - Shows emotionally charged words
        • **Provide Explanations** - Gives clear reasoning for decisions
        
        **Bias Types Detected:**
        - Left/Right Political Bias
        - Neutral
        - Sensational
        - Emotional
        - Clickbait
        """)
        
        st.header("⚠️ Disclaimer")
        st.markdown("""
        This tool uses AI for analysis and may not be 100% accurate. 
        Always verify information from multiple reliable sources.
        """)
        
        # Clear results button
        if st.session_state.analysis_result:
            if st.button("🗑️ Clear Results"):
                st.session_state.analysis_result = None
                st.session_state.article_text = ""
                st.session_state.current_url = None
                st.session_state.article_title = ""
                st.session_state.domain_credibility = None
                st.session_state.input_key += 1
                st.rerun()

if __name__ == "__main__":
    main()
