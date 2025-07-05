# Search and Scrape System

This is a modular system for searching DuckDuckGo and scraping content from the found URLs.

## Files

### Core Modules

1. **`duckduckgo_search.py`** - Handles DuckDuckGo search and URL extraction
   - `search_duckduckgo(query, num_results=5)` - Search DuckDuckGo and return URLs
   - `is_valid_search_url(url)` - Validate if URL is a legitimate search result

2. **`content_scraper.py`** - Handles content scraping from URLs
   - `scrape_content(url)` - Scrape content from a single URL
   - `scrape_multiple_urls(urls, save_to_files=True, output_dir="scraped_content")` - Scrape multiple URLs
   - `extract_content_advanced(soup, url)` - Advanced content extraction strategies
   - `clean_content(content)` - Clean and format extracted content

3. **`search_and_scrape.py`** - Combined workflow script
   - `search_and_scrape(query, num_results=5, save_to_files=True, output_dir="search_results")` - Complete workflow
   - `main()` - Command-line interface

## Usage

### Option 1: Use the combined script (Recommended)
```bash
cd backend
python search_and_scrape.py
```

This will prompt you for:
- Search query
- Number of results (default: 5)
- Whether to save results to files

### Option 2: Use modules separately

#### Search only:
```python
from duckduckgo_search import search_duckduckgo

urls = search_duckduckgo("your search query", 5)
print(urls)
```

#### Scrape only:
```python
from content_scraper import scrape_multiple_urls

urls = ["https://example.com", "https://example.org"]
results = scrape_multiple_urls(urls, save_to_files=True, output_dir="my_results")
```

#### Combined workflow:
```python
from search_and_scrape import search_and_scrape

results = search_and_scrape("your query", 5, save_to_files=True, output_dir="results")
```

## Output

When saving to files, the system creates:
- `complete_results.json` - Complete results with all data
- `summary_report.txt` - Human-readable summary
- Individual content files for each scraped URL
- `scraping_summary.json` - Summary of scraping results

## Requirements

Make sure you have the required dependencies installed:
```bash
pip install -r requirements.txt
```

## Features

- **Modular Design**: Separate concerns for search and scraping
- **Robust URL Filtering**: Filters out ads and invalid URLs
- **Multiple Extraction Strategies**: Uses various methods to extract content
- **Content Cleaning**: Removes unwanted elements and formats text
- **File Output**: Saves results in multiple formats
- **Error Handling**: Graceful handling of failed requests
- **Progress Tracking**: Shows progress during operations 