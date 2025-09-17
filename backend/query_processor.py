"""
Query Processor - Integrates all modular components for the /query endpoint
"""

from simplexity_classifier import get_simplexity_classifier
from embeddings import get_embedding
from db import query_db, add_to_db
from duckduckgo_search import search_duckduckgo
from content_scraper import scrape_multiple_urls
from summarizer import summarize
from focused_extractor import extract_focused_content
from typing import Dict, Any, Callable, Optional
import time
import os
import asyncio

class QueryProcessor:
    """Main query processor that orchestrates the entire workflow"""
    
    def __init__(self, cache_threshold: float = 0.7, max_search_results: int = 5):
        self.cache_threshold = cache_threshold
        self.max_search_results = max_search_results
    
    async def process_query(self, query: str, status_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None) -> Dict:
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
        self._emit_status(status_callback, "validating", {"query": query})
        
        # Step 1: Validate query
        print("Step 1: Classifying query...")
        classifier = get_simplexity_classifier()
        classification_result = await asyncio.to_thread(classifier.classify_query, query)
        is_valid = classification_result.is_valid
        is_time_sensitive = classification_result.is_time_sensitive
        print(f"Classification result: {is_valid} (Confidence: {classification_result.confidence:.2f}, Intent: {classification_result.intent}, Time-sensitive: {is_time_sensitive})")
        
        # Emit status immediately after classification
        if status_callback:
            await status_callback("classifying", {"query": query, "is_valid": is_valid, "is_time_sensitive": is_time_sensitive})
        
        
        if not is_valid:
            print("❌ Query rejected by classifier - stopping pipeline")
            self._emit_status(status_callback, "invalid", {"reason": "classifier_rejected"})
            return {
                "valid": False,
                "is_valid": False,
                "is_time_sensitive": False,
                "summary": "Query invalid",
                "from_cache": False,
                "cached_query": None,
                "urls_found": 0,
                "content_scraped": 0,
                "processing_time": time.time() - start_time,
                "search_time": 0.0,
                "scrape_time": 0.0,
                "cache_similarity": 0.0,
                "error": "Query classification failed"
            }
        
        print("✅ Query passed classification - continuing pipeline")
        
        # Step 2: Check cache (only for valid and time-insensitive queries)
        if not is_time_sensitive:
            print(f"Step 2: Checking cache (time-insensitive query)...")
            print(f"  Query: '{query}'")
            print(f"  Cache threshold: {self.cache_threshold}")
            await self._emit_status_async(status_callback, "similarity", {"info": "checking_cache"})
            cache_result = await self._check_cache_async(query)
            
            if cache_result['hit']:
                print(f"✅ Cache hit - serving from cache")
                print(f"  Similarity score: {cache_result['similarity']:.3f}")
                print(f"  Cached query: '{cache_result.get('cached_query', 'Unknown')}'")
                await self._emit_status_async(status_callback, "cache_hit", {"similarity": cache_result['similarity'], "cached_query": cache_result.get('cached_query')})
                await self._emit_status_async(status_callback, "done", {"from_cache": True})
                return {
                    "valid": True,
                    "is_valid": True,
                    "is_time_sensitive": False,
                    "summary": cache_result['summary'],
                    "from_cache": True,
                    "cached_query": cache_result.get('cached_query', 'Unknown'),
                    "urls_found": 0,
                    "content_scraped": 0,
                    "scraped_urls": [],  # Add this missing field
                    "processing_time": time.time() - start_time,
                    "search_time": 0.0,
                    "scrape_time": 0.0,
                    "cache_similarity": cache_result['similarity']
                }
            else:
                print(f"❌ Cache miss - proceeding to search and scrape")
                print(f"  No similar queries found above threshold {self.cache_threshold}")
        else:
            print(f"Step 2: Skipping cache (time-sensitive query) - proceeding to search and scrape")
            print(f"  Query: '{query}' is time-sensitive, cache bypassed")
        
        # Step 3: Search and scrape
        print("Step 3: Searching and scraping...")
        await self._emit_status_async(status_callback, "searching", {"info": "web_search"})
        search_results = await self._search_and_scrape_async(query)
        
        # Step 4: Extract focused content from scraped data
        print("Step 4: Extracting focused content...")
        await self._emit_status_async(status_callback, "scraping", {"info": "content_extraction"})
        extraction_start = time.time()
        
        # Try Groq first, fallback to TextRank if not available
        extraction_method = "groq" if os.getenv("GROQ_API_KEY") else "textrank"
        print(f"Using extraction method: {extraction_method}")
        
        focused_texts = await asyncio.to_thread(
            extract_focused_content,
            query=query,
            texts=search_results['texts'],
            method=extraction_method,
            sentences_ratio=0.3
        )
        
        extraction_time = time.time() - extraction_start
        print(f"✅ Focused extraction complete - reduced from {len(search_results['texts'])} to {len(focused_texts)} sources")
        
        print("Step 5: Generating summary from focused content...")
        await self._emit_status_async(status_callback, "summarizing", {"info": "ai_analysis"})
        summary = await asyncio.to_thread(summarize, focused_texts, query)
        
        # Step 7: Cache results
        print("Step 6: Caching results...")
        await self._cache_results_async(query, summary, is_time_sensitive)
        
        print("✅ Pipeline completed successfully")
        await self._emit_status_async(status_callback, "done", {"from_cache": False})
        
        return {
            "valid": True,
            "is_valid": True,
            "is_time_sensitive": is_time_sensitive,
            "summary": summary,
            "from_cache": False,
            "cached_query": None,
            "urls_found": search_results['urls_found'],
            "content_scraped": search_results['content_scraped'],
            "scraped_urls": search_results.get('scraped_urls', []),
            "processing_time": time.time() - start_time,
            "search_time": search_results['search_time'],
            "scrape_time": search_results['scrape_time'],
            "cache_similarity": 0.0
        }
    
    def _check_cache(self, query: str) -> Dict:
        """Check if query exists in cache with similarity threshold"""
        print(f"  🔍 Checking cache for query: '{query}'")
        
        try:
            # Generate embedding for the query
            print(f"  📊 Generating embedding...")
            embedding = get_embedding(query)
            print(f"  ✅ Embedding generated successfully")
            
            # Query the cache with similarity threshold
            print(f"  🔎 Searching cache with threshold: {self.cache_threshold}")
            results = query_db(embedding, query_text=query, top_k=3, similarity_threshold=self.cache_threshold)
            
            if results and results['documents'] and results['documents'][0]:
                # Get the best match
                best_similarity = results['metadatas'][0].get('similarity', 0) if results['metadatas'] else 0
                cached_query = results['metadatas'][0].get('query', 'Unknown') if results['metadatas'] else 'Unknown'
                
                print(f"  🎯 Cache hit found!")
                print(f"    Original cached query: '{cached_query}'")
                print(f"    Current query: '{query}'")
                print(f"    Similarity score: {best_similarity:.3f}")
                print(f"    Threshold: {self.cache_threshold}")
                print(f"    ✅ Similarity {best_similarity:.3f} >= threshold {self.cache_threshold}")
                
                return {
                    'hit': True,
                    'summary': results['documents'][0],
                    'similarity': best_similarity,
                    'cached_query': cached_query
                }
            else:
                print(f"  ❌ No cache results found")
                print(f"    Query: '{query}'")
                print(f"    Threshold: {self.cache_threshold}")
                print(f"    Results: {results}")
                return {'hit': False}
                
        except Exception as e:
            print(f"  💥 Error during cache check: {e}")
            return {'hit': False}
    
    def _search_and_scrape(self, query: str) -> Dict:
        """Search DuckDuckGo and scrape content from found URLs in parallel"""
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
        
        print(f"Found {len(urls)} URLs, starting parallel scraping...")
        
        # Scrape content in parallel
        scrape_start = time.time()
        
        # Use parallel scraping with max_workers=3 (can be adjusted)
        max_workers = min(3, len(urls))  # Don't use more workers than URLs
        scrape_results = scrape_multiple_urls(urls, save_to_files=False, output_dir="scraped_content", max_workers=max_workers)
        
        # Extract successful content
        texts = []
        successful_scrapes = 0
        
        for result in scrape_results:
            if result['success']:
                texts.append(result['content'])
                successful_scrapes += 1
        
        scrape_time = time.time() - scrape_start
        
        print(f"Parallel scraping complete: {successful_scrapes}/{len(urls)} successful in {scrape_time:.2f}s")
        
        return {
            'urls_found': len(urls),
            'content_scraped': successful_scrapes,
            'texts': texts,
            'urls': urls,
            'scraped_urls': [result['url'] for result in scrape_results if result['success']],
            'search_time': search_time,
            'scrape_time': scrape_time
        }
    
    def _cache_results(self, query: str, summary: str, is_time_sensitive: bool = False):
        """Cache the query and summary (only for time-insensitive queries)"""
        if is_time_sensitive:
            print(f"Skipping cache for time-sensitive query: {query}")
            return
            
        try:
            embedding = get_embedding(query)
            add_to_db(embedding, summary, metadata={"query": query})
            print(f"Cached results for query: {query}")
        except Exception as e:
            print(f"Error caching results: {e}")

    def _emit_status(self, callback: Optional[Callable[[str, Dict[str, Any]], None]], step: str, data: Dict[str, Any]):
        """Emit a status update if a callback is provided"""
        if callback is None:
            return
        try:
            callback(step, data)
        except Exception as emit_error:
            print(f"Warning: failed to emit status '{step}': {emit_error}")
    
    async def _emit_status_async(self, callback: Optional[Callable[[str, Dict[str, Any]], None]], step: str, data: Dict[str, Any]):
        """Async helper to emit status updates if callback is provided"""
        if callback is None:
            return
        try:
            await callback(step, data)
        except Exception as emit_error:
            print(f"Warning: failed to emit async status '{step}': {emit_error}")
    
    async def _check_cache_async(self, query: str) -> Dict:
        """Async version of cache check"""
        return await asyncio.to_thread(self._check_cache, query)
    
    async def _search_and_scrape_async(self, query: str) -> Dict:
        """Async version of search and scrape"""
        return await asyncio.to_thread(self._search_and_scrape, query)
    
    async def _cache_results_async(self, query: str, summary: str, is_time_sensitive: bool = False):
        """Async version of cache results"""
        await asyncio.to_thread(self._cache_results, query, summary, is_time_sensitive)

# Global instance for use in FastAPI endpoints
query_processor = QueryProcessor()