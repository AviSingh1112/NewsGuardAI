import json
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from typing import Dict, Optional

def generate_json_report(analysis_result: Dict, article_text: str, url: Optional[str] = None, 
                        domain_credibility: Optional[Dict] = None) -> str:
    """
    Generate a JSON report of the analysis
    
    Args:
        analysis_result: The analysis result dictionary
        article_text: The article text that was analyzed
        url: Optional URL of the article
        domain_credibility: Optional domain credibility score
        
    Returns:
        JSON string of the report
    """
    report = {
        'analysis_timestamp': datetime.now().isoformat(),
        'article_info': {
            'url': url if url else 'Direct text input',
            'text_preview': article_text[:500] + '...' if len(article_text) > 500 else article_text,
            'word_count': len(article_text.split())
        },
        'verdict': {
            'result': analysis_result.get('verdict', 'Unknown'),
            'confidence': analysis_result.get('confidence', 0),
            'explanation': analysis_result.get('explanation', '')
        },
        'bias_analysis': {
            'bias_type': analysis_result.get('bias_type', 'Unknown'),
            'biased_words': analysis_result.get('biased_words', [])
        }
    }
    
    # Add domain credibility if available
    if domain_credibility and domain_credibility.get('score') is not None:
        report['source_credibility'] = {
            'domain': domain_credibility.get('domain', ''),
            'score': domain_credibility.get('score', 0),
            'category': domain_credibility.get('category', ''),
            'explanation': domain_credibility.get('explanation', ''),
            'recommendation': domain_credibility.get('recommendation', '')
        }
    
    return json.dumps(report, indent=2)

def generate_pdf_report(analysis_result: Dict, article_text: str, url: Optional[str] = None,
                       article_title: Optional[str] = None, domain_credibility: Optional[Dict] = None) -> BytesIO:
    """
    Generate a PDF report of the analysis
    
    Args:
        analysis_result: The analysis result dictionary
        article_text: The article text that was analyzed
        url: Optional URL of the article
        article_title: Optional title of the article
        domain_credibility: Optional domain credibility score
        
    Returns:
        BytesIO object containing the PDF
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a237e'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#283593'),
        spaceAfter=12,
        spaceBefore=12
    )
    
    normal_style = styles['BodyText']
    
    # Title
    elements.append(Paragraph("AI-Powered Fake News & Bias Detection Report", title_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Timestamp
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    elements.append(Paragraph(f"<b>Report Generated:</b> {timestamp}", normal_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Article Information
    elements.append(Paragraph("Article Information", heading_style))
    
    if article_title:
        elements.append(Paragraph(f"<b>Title:</b> {article_title}", normal_style))
    
    if url:
        elements.append(Paragraph(f"<b>URL:</b> {url[:80]}...", normal_style))
    else:
        elements.append(Paragraph("<b>Source:</b> Direct text input", normal_style))
    
    word_count = len(article_text.split())
    elements.append(Paragraph(f"<b>Word Count:</b> {word_count} words", normal_style))
    elements.append(Spacer(1, 0.3*inch))
    
    # Analysis Results
    elements.append(Paragraph("Analysis Results", heading_style))
    
    verdict = analysis_result.get('verdict', 'Unknown')
    confidence = analysis_result.get('confidence', 0)
    bias_type = analysis_result.get('bias_type', 'Unknown')
    
    # Verdict table
    verdict_color = colors.green if verdict == 'REAL' else colors.red if verdict == 'FAKE' else colors.orange
    
    verdict_data = [
        ['Metric', 'Result'],
        ['Verdict', verdict],
        ['Confidence', f'{confidence}%'],
        ['Bias Type', bias_type]
    ]
    
    verdict_table = Table(verdict_data, colWidths=[2.5*inch, 3.5*inch])
    verdict_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#283593')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (1, 1), (1, 1), verdict_color.clone(alpha=0.3)),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')])
    ]))
    
    elements.append(verdict_table)
    elements.append(Spacer(1, 0.2*inch))
    
    # Explanation
    elements.append(Paragraph("Explanation", heading_style))
    explanation = analysis_result.get('explanation', 'No explanation provided.')
    elements.append(Paragraph(explanation, normal_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Domain Credibility (if available)
    if domain_credibility and domain_credibility.get('score') is not None:
        elements.append(Paragraph("Source Credibility", heading_style))
        
        domain_score = domain_credibility.get('score', 0)
        domain_category = domain_credibility.get('category', 'Unknown')
        domain_name = domain_credibility.get('domain', 'N/A')
        
        domain_data = [
            ['Metric', 'Result'],
            ['Domain', domain_name],
            ['Credibility Score', f'{domain_score}/100'],
            ['Category', domain_category]
        ]
        
        domain_table = Table(domain_data, colWidths=[2.5*inch, 3.5*inch])
        domain_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#283593')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')])
        ]))
        
        elements.append(domain_table)
        elements.append(Spacer(1, 0.1*inch))
        
        domain_explanation = domain_credibility.get('explanation', '')
        if domain_explanation:
            elements.append(Paragraph(f"<i>{domain_explanation}</i>", normal_style))
        
        elements.append(Spacer(1, 0.2*inch))
    
    # Biased Words
    biased_words = analysis_result.get('biased_words', [])
    if biased_words:
        elements.append(Paragraph("Identified Biased/Emotionally Charged Words", heading_style))
        
        biased_words_text = ", ".join(biased_words[:15])
        elements.append(Paragraph(biased_words_text, normal_style))
        elements.append(Spacer(1, 0.2*inch))
    
    # Article Preview
    elements.append(Paragraph("Article Text Preview", heading_style))
    preview_text = article_text[:800] + '...' if len(article_text) > 800 else article_text
    elements.append(Paragraph(preview_text, normal_style))
    elements.append(Spacer(1, 0.3*inch))
    
    # Disclaimer
    elements.append(Paragraph("Disclaimer", heading_style))
    disclaimer_text = """
    This analysis is generated by an AI model and should be used as a guide only. 
    The results may not be 100% accurate. Always verify information from multiple reliable sources 
    before drawing conclusions about the authenticity or bias of any article.
    """
    elements.append(Paragraph(disclaimer_text, normal_style))
    
    # Build PDF
    doc.build(elements)
    
    # Get the PDF from the buffer
    buffer.seek(0)
    return buffer

# Test functions
def test_json_export():
    """Test JSON export"""
    test_result = {
        'verdict': 'FAKE',
        'confidence': 85,
        'bias_type': 'Sensational',
        'explanation': 'This article contains multiple sensational claims without proper sourcing.',
        'biased_words': ['shocking', 'unbelievable', 'crisis']
    }
    
    test_text = "BREAKING NEWS: This shocking discovery will change everything!"
    test_url = "https://example.com/fake-article"
    
    test_domain_cred = {
        'domain': 'example.com',
        'score': 30,
        'category': 'Low Credibility',
        'explanation': 'Known for unreliable reporting',
        'recommendation': 'Verify all claims'
    }
    
    json_report = generate_json_report(test_result, test_text, test_url, test_domain_cred)
    print("JSON Report Generated:")
    print(json_report)

def test_pdf_export():
    """Test PDF export"""
    test_result = {
        'verdict': 'FAKE',
        'confidence': 85,
        'bias_type': 'Sensational',
        'explanation': 'This article contains multiple sensational claims without proper sourcing.',
        'biased_words': ['shocking', 'unbelievable', 'crisis', 'breaking']
    }
    
    test_text = "BREAKING NEWS: This shocking discovery will change everything! Scientists have made an unbelievable breakthrough."
    test_url = "https://example.com/fake-article"
    test_title = "Shocking Discovery Changes Everything"
    
    test_domain_cred = {
        'domain': 'example.com',
        'score': 30,
        'category': 'Low Credibility',
        'explanation': 'Known for unreliable reporting',
        'recommendation': 'Verify all claims'
    }
    
    pdf_buffer = generate_pdf_report(test_result, test_text, test_url, test_title, test_domain_cred)
    
    # Save to file for testing
    with open('test_report.pdf', 'wb') as f:
        f.write(pdf_buffer.getvalue())
    
    print("PDF Report Generated: test_report.pdf")

if __name__ == "__main__":
    print("Testing JSON Export:")
    test_json_export()
    print("\n" + "="*80 + "\n")
    print("Testing PDF Export:")
    test_pdf_export()
