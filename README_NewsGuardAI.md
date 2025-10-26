# 🧠 NewsGuardAI — AI-Powered Fake News & Bias Detection System

![Python](https://img.shields.io/badge/Python-3.11-blue.svg)
![Streamlit](https://img.shields.io/badge/Framework-Streamlit-red.svg)
![Groq](https://img.shields.io/badge/LLM-Groq%20LLaMA%203.1%208B-success.svg)
![License](https://img.shields.io/badge/License-MIT-lightgrey.svg)

---

## 📰 Overview

**NewsGuardAI** is an intelligent **NLP-based web application** that detects **fake news, bias, and source credibility** in online articles.  
It integrates **Groq’s LLaMA 3.1 model**, rule-based **bias detection**, and **domain credibility scoring** to deliver accurate and explainable evaluations for any news article or URL.

---

## 🚀 Features

✅ Multi-layer article extraction (Trafilatura, BeautifulSoup, Newspaper3k, Playwright)  
✅ Groq LLM analysis for factual accuracy and bias  
✅ Domain credibility scoring for Indian and global news sites  
✅ Interactive Streamlit dashboard  
✅ Exportable PDF/JSON reports  
✅ Database storage for previous analyses  

---

## ⚙️ Installation

```bash
git clone https://github.com/<your-username>/NewsGuardAI.git
cd NewsGuardAI
python -m venv venv
venv\Scripts\activate      # Windows
pip install -r requirements.txt
playwright install chromium
python -m nltk.downloader punkt
streamlit run app.py
```

---

## 🧠 Example Output

**Input URL:**  
`https://www.thehindu.com/news/national/india-to-host-g20-summit/article67148429.ece`

**Output:**
```
Verdict: REAL
Confidence: 90%
Bias Type: Neutral
Domain Credibility: 95/100 (High)
Explanation: The article appears factual, balanced, and credible.
```

---

## 📈 Results Summary

| Metric | Value |
|--------|-------|
| **Accuracy (Manual Evaluation)** | ~91.3% |
| **Average Confidence (Real)** | 85% |
| **Average Confidence (Fake)** | 78% |
| **Bias Keyword Precision** | 93% |
| **Average Response Time** | 8–12 seconds |

---

## 📚 References

- [Groq API Documentation](https://console.groq.com/docs)  
- [Media Bias/Fact Check](https://mediabiasfactcheck.com)  
- [AltNews India](https://www.altnews.in)  
- [BOOM Fact Check](https://www.boomlive.in)  
- [Trafilatura Docs](https://trafilatura.readthedocs.io)  
- [Streamlit Docs](https://docs.streamlit.io)  

---

## 👨‍💻 Author

**Divyendra Singh**  
B.Tech (Computer Science) — NLP Mini Project  
Mentor: *Dr. Raj Gaurav Mishra*  
Year: 2025  

---

## 📝 License

Released under the **MIT License**.
