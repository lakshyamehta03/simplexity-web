# Simplexity Query Agent

An intelligent web query agent that validates, searches, scrapes, and summarizes information from the web, with caching for fast repeated queries. 

---

## Features
- **Query Validation**: Filters out unsupported or irrelevant queries
- **Semantic Caching**: Use cached answers for repeated or similar queries.
- **Web Search & Scraping**: Finds and extracts content from top 5 results from duckduckgo using headless browser automation.
- **Focused Content Extractor**: Extracts relevant content for the summarizer from scraped content.
- **AI Summarization**: Generates concise, relevant answers using GROQ LLMs.
- **Modular Design**: Each stage is a separate, testable module for easy maintenance and extension.

---

## 🏗️ Architecture

![Architecture Diagram](architecture.png)

**File Mapping for Each Stage:**

| Stage                        | Main Files/Modules                                 |
|------------------------------|----------------------------------------------------|
| **User Input**               | `main.py`                                          |
| **Query Validator**          | `backend/classifier.py`                            |
| **Embed Query**              | `backend/embeddings.py`                            |
| **Vector DB Similarity**     | `backend/db.py`, `backend/embeddings.py`           |
| **Web Search**               | `backend/duckduckgo_search.py`                     |
| **Scrape Top 5 URLs**        | `backend/content_scraper.py`                       |
| **Summarize Results**        | `backend/summarizer.py`                            |
| **Store in DB**              | `backend/db.py`                                    |
| **Return Summary**           | `main.py`,                                         |

---

## 📦 Project Structure

```
/
├── backend/
│   ├── main.py                # FastAPI entry point
│   ├── classifier.py          # Query validation
│   ├── embeddings.py          # Embedding generation
│   ├── db.py                  # Vector DB logic
│   ├── duckduckgo_search.py   # Web search
│   ├── content_scraper.py     # Web scraping
│   ├── summarizer.py          # Summarization
│   └── queries.csv            # Valid/invalid query examples
├── frontend/                  # React frontend (UI, stepper, results)
├── README.md
└── ...
```

## 💻 Tech Stack

- **Backend**: FastAPI
- **Frontend**: React, TypeScript
- **Vector DB**: ChromaDB
- **Web Scraping**: Selenium, BeautifulSoup
- **LLM**: GROQ LLMs (for summarization)
- **Frontend**: React, TypeScript, Material-UI
- **Styling**: CSS Modules, TailwindCSS

---