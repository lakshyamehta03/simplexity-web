"""
Query Processor - Integrates all modular components for the /query endpoint
"""

from classifier import is_valid_query
from embeddings import get_embedding
from db import query_db, add_to_db
from duckduckgo_search import search_duckduckgo
from content_scraper import scrape_content
from summarizer import summarize
from typing import Dict, List
import time

class QueryProcessor:
    """Main query processor that orchestrates the entire workflow"""
    
    def __init__(self, cache_threshold: float = 0.8, max_search_results: int = 5):
        self.cache_threshold = cache_threshold
        self.max_search_results = max_search_results
    
    def process_query(self, query: str) -> Dict:
        """
        Process a query through the complete pipeline:
        1. Validate query
        2. Check cache
        3. Search and scrape if needed
        4. Generate summary
        5. Cache results
        
        Returns:
            Dict with processing results
        """
        start_time = time.time()
        
        print(f"\n=== PROCESSING QUERY: '{query}' ===")
        
        # Step 1: Validate query
        print("Step 1: Classifying query...")
        is_valid = is_valid_query(query)
        print(f"Classification result: {is_valid}")
        
        if not is_valid:
            print("❌ Query rejected by classifier - stopping pipeline")
            return {
                "valid": False,
                "summary": "Query invalid",
                "from_cache": False,
                "urls_found": 0,
                "content_scraped": 0,
                "processing_time": time.time() - start_time,
                "error": "Query classification failed"
            }
        
        print("✅ Query passed classification - continuing pipeline")
        
        # Step 2: Check cache
        print("Step 2: Checking cache...")
        cache_result = self._check_cache(query)
        if cache_result['hit']:
            print("✅ Cache hit - serving from cache")
            return {
                "valid": True,
                "summary": cache_result['summary'],
                "from_cache": True,
                "urls_found": 0,
                "content_scraped": 0,
                "processing_time": time.time() - start_time,
                "cache_similarity": cache_result['similarity']
            }
        
        print("❌ Cache miss - proceeding to search and scrape")
        
        # Step 3: Search and scrape
        print("Step 3: Searching and scraping...")
        search_results = self._search_and_scrape(query)
        
        # Step 4: Generate summary
        print("Step 4: Generating summary...")
        summary = summarize(search_results['texts'], query)
        
        # Step 5: Cache results
        print("Step 5: Caching results...")
        self._cache_results(query, summary)
        
        print("✅ Pipeline completed successfully")
        
        return {
            "valid": True,
            "summary": summary,
            "from_cache": False,
            "urls_found": search_results['urls_found'],
            "content_scraped": search_results['content_scraped'],
            "processing_time": time.time() - start_time,
            "search_time": search_results['search_time'],
            "scrape_time": search_results['scrape_time']
        }
    
    def _check_cache(self, query: str) -> Dict:
        """Check if query exists in cache with similarity threshold"""
        embedding = get_embedding(query)
        results = query_db(embedding, query_text=query, top_k=1, similarity_threshold=self.cache_threshold)
        
        if results and results['documents'] and results['documents'][0]:
            return {
                'hit': True,
                'summary': results['documents'][0],
                'similarity': results['metadatas'][0].get('similarity', 0) if results['metadatas'] else 0
            }
        
        return {'hit': False}
    
    def _search_and_scrape(self, query: str) -> Dict:
        """Search DuckDuckGo and scrape content from found URLs"""
        search_start = time.time()
        
        # Search for URLs
        print(f"Searching for: '{query}'")
        urls = search_duckduckgo(query, self.max_search_results)
        search_time = time.time() - search_start
        
        if not urls:
            return {
                'urls_found': 0,
                'content_scraped': 0,
                'texts': [],
                'search_time': search_time,
                'scrape_time': 0
            }
        
        print(f"Found {len(urls)} URLs, starting to scrape...")
        
        # Scrape content
        scrape_start = time.time()
        texts = []
        successful_scrapes = 0
        
        for i, url in enumerate(urls, 1):
            print(f"Scraping {i}/{len(urls)}: {url}")
            try:
                content = scrape_content(url)
                if content and len(content.strip()) > 100:
                    texts.append(content)
                    successful_scrapes += 1
                    print(f"✓ Scraped {len(content)} characters")
                else:
                    print(f"✗ Insufficient content")
            except Exception as e:
                print(f"✗ Error scraping {url}: {e}")
        
        scrape_time = time.time() - scrape_start
        
        print(f"Scraping complete: {successful_scrapes}/{len(urls)} successful")
        
        return {
            'urls_found': len(urls),
            'content_scraped': successful_scrapes,
            'texts': texts,
            'search_time': search_time,
            'scrape_time': scrape_time
        }
    
    def _cache_results(self, query: str, summary: str):
        """Cache the query and summary"""
        try:
            embedding = get_embedding(query)
            add_to_db(embedding, summary, metadata={"query": query})
            print(f"Cached results for query: {query}")
        except Exception as e:
            print(f"Error caching results: {e}")
    
    def search_only(self, query: str) -> Dict:
        """Search only - no scraping"""
        urls = search_duckduckgo(query, self.max_search_results)
        return {
            "query": query,
            "urls_found": len(urls),
            "urls": urls
        }
    
    def scrape_only(self, urls: List[str]) -> Dict:
        """Scrape only - no search"""
        results = []
        successful_scrapes = 0
        
        for url in urls:
            try:
                content = scrape_content(url)
                success = bool(content and len(content.strip()) > 100)
                if success:
                    successful_scrapes += 1
                
                results.append({
                    "url": url,
                    "content_length": len(content) if content else 0,
                    "success": success
                })
            except Exception as e:
                results.append({
                    "url": url,
                    "content_length": 0,
                    "success": False,
                    "error": str(e)
                })
        
        return {
            "urls_processed": len(urls),
            "results": results,
            "successful_scrapes": successful_scrapes
        }

# Global instance for use in FastAPI endpoints
query_processor = QueryProcessor() 