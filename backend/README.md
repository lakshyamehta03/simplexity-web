# Search and Scrape System

This is a modular system for searching DuckDuckGo and scraping content from the found URLs.

## Core Modules

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

## Features

- **Modular Design**: Separate concerns for search and scraping
- **Robust URL Filtering**: Filters out ads and invalid URLs
- **Multiple Extraction Strategies**: Uses various methods to extract content
- **Content Cleaning**: Removes unwanted elements and formats text
- **File Output**: Saves results in multiple formats
- **Error Handling**: Graceful handling of failed requests
- **Progress Tracking**: Shows progress during operations 