# Ripplica Query Core

An intelligent, modular web query agent that validates, searches, scrapes, and summarizes information from the web, with semantic caching for fast repeated queries.

---

## 🚀 Features
- **Query Validation**: Filters out unsupported or irrelevant queries using semantic similarity and rules.
- **Semantic Caching**: Uses vector similarity to return instant answers for repeated or similar queries.
- **Web Search & Scraping**: Finds and extracts content from top web results using headless browser automation.
- **AI Summarization**: Generates concise, relevant answers using transformer models.
- **Modular Design**: Each stage is a separate, testable module for easy maintenance and extension.

---

## 🏗️ Architecture

The system is designed as a pipeline of independent modules, each responsible for a single stage of the query process. This modularity makes the system robust, testable, and easy to extend.

```
User (UI/CLI)
   |
   v
Query Validator (classifier.py)
   |-- invalid --> Respond: Invalid Query
   |
   v
Embed Query (embeddings.py)
   |
   v
Vector DB Similarity Search (db.py + embeddings.py)
   |-- match found --> Return Stored Summary
   |
   v
Web Search (duckduckgo_search.py)
   |
   v
Scrape Top 5 URLs (content_scraper.py)
   |
   v
Summarize Results (summarizer.py)
   |
   v
Store (db.py)
   |
   v
Return Summary to User
```

**File Mapping for Each Stage:**

| Stage                        | Main Files/Modules                                 |
|------------------------------|----------------------------------------------------|
| **User Input**               | `main.py`, `frontend/`                             |
| **Query Validator**          | `backend/classifier.py`                            |
| **Embed Query**              | `backend/embeddings.py`                            |
| **Vector DB Similarity**     | `backend/db.py`, `backend/embeddings.py`           |
| **Web Search**               | `backend/duckduckgo_search.py`                     |
| **Scrape Top 5 URLs**        | `backend/content_scraper.py`                       |
| **Summarize Results**        | `backend/summarizer.py`                            |
| **Store in DB**              | `backend/db.py`                                    |
| **Return Summary**           | `main.py`, `frontend/`                             |

---

## 🛠️ Engineering Choices

### 1. **Why ChromaDB?**
ChromaDB is used as the vector database for semantic caching and similarity search. It is lightweight, fast, and easy to integrate with Python. ChromaDB allows us to store embeddings and perform efficient nearest-neighbor searches, enabling instant responses for repeated or similar queries. This greatly improves performance and user experience compared to traditional keyword-based caching.

### 2. **Why FastAPI?**
FastAPI is chosen for the backend because it is modern, fast, and developer-friendly. It provides automatic data validation, async support, and easy API documentation. FastAPI's modularity and performance make it ideal for building scalable, production-ready APIs that can serve both the frontend and other clients.

### 3. **Why These Models?**
- **Sentence-Transformers (all-MiniLM-L6-v2):** Used for generating semantic embeddings of queries and documents. This model is lightweight, fast, and provides high-quality embeddings for similarity search and classification.
- **BART (facebook/bart-large-cnn):** Used for summarization. BART is a transformer-based model that balances speed and quality, making it suitable for generating concise, relevant summaries from scraped web content.

### 4. **Modular Pipeline**
Each stage (validation, embedding, search, scraping, summarization, caching) is a separate module. This makes the system easy to test, debug, and extend (e.g., swap out the search engine or summarizer).

### 5. **Semantic Query Validation**
Uses a combination of rule-based and semantic similarity checks (with sentence-transformers) to robustly filter out unsupported queries. The examples in `queries.csv` can be easily updated to tune what is considered valid/invalid.

### 6. **Vector Database for Caching**
Uses vector similarity search to instantly answer repeated or similar queries, saving compute and improving user experience. Embeddings are generated with `sentence-transformers` and stored alongside summaries.

### 7. **Headless Web Scraping**
Uses Selenium and BeautifulSoup for robust, dynamic content extraction from real web pages. Multiple extraction strategies and aggressive cleaning ensure high-quality, relevant content.

### 8. **Transformer-based Summarization**
Uses a fast, open-source transformer model (BART) for summarization, balancing speed and quality. Summarization is query-focused for relevance.

### 9. **Frontend-Backend Separation**
The React frontend is decoupled from the FastAPI backend, communicating via a clean API. The frontend stepper UI reflects backend progress and results.

---

## 📦 Project Structure

```
ripplica-query-core-main/
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
├── README.md                  # This documentation
└── ...
```

---

## ⚡ Getting Started

### 1. **Clone the repo**
```sh
git clone https://github.com/lakshyamehta03/ripplica-query-core.git
cd ripplica-query-core
```

### 2. **Backend Setup**
```sh
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### 3. **Frontend Setup**
```sh
cd ../frontend
npm install
npm run dev
```

---

## 📝 Example Flow

1. **User submits a query** via the UI or CLI.
2. **Query is validated** (`classifier.py`). If invalid, user is notified.
3. **Query is embedded** (`embeddings.py`).
4. **Cache is checked** (`db.py`). If a similar query is found, the stored summary is returned instantly.
5. **If no cache match**:
    - **Web search** is performed (`duckduckgo_search.py`).
    - **Top URLs are scraped** (`content_scraper.py`).
    - **Content is summarized** (`summarizer.py`).
    - **Result is cached** (`db.py`) and returned to the user.