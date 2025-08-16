"""
Query Processor - Integrates all modular components for the /query endpoint
"""

from perplexity_classifier import get_perplexity_classifier, ClassificationResult
from embeddings import get_embedding
from db import query_db, add_to_db
from duckduckgo_search import search_duckduckgo
from content_scraper import scrape_content, scrape_multiple_urls
from summarizer import summarize
from focused_extractor import extract_focused_content, save_focused_content
from typing import Dict, List, Any
import time
import os

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
        classifier = get_perplexity_classifier()
        classification_result = classifier.classify_query(query)
        is_valid = classification_result.is_valid
        print(f"Classification result: {is_valid} (Confidence: {classification_result.confidence:.2f}, Intent: {classification_result.intent})")
        
        
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
        
        # Step 4: Extract focused content from scraped data
        print("Step 4: Extracting focused content...")
        extraction_start = time.time()
        
        # Try Groq first, fallback to TextRank if not available
        extraction_method = "groq" if os.getenv("GROQ_API_KEY") else "textrank"
        print(f"Using extraction method: {extraction_method}")
        
        focused_texts = extract_focused_content(
            query=query,
            texts=search_results['texts'],
            method=extraction_method,
            sentences_ratio=0.3
        )
        
        extraction_time = time.time() - extraction_start
        print(f"✅ Focused extraction complete - reduced from {len(search_results['texts'])} to {len(focused_texts)} sources")
        
        # Step 5: Save both original and focused content for comparison
        print("Step 5: Saving content for analysis...")
        try:
            os.makedirs("scraped_content", exist_ok=True)
            
            # Save original combined content
            combined_content_file = "scraped_content/combined_content_for_summarizer.txt"
            with open(combined_content_file, 'w', encoding='utf-8') as f:
                f.write(f"Query: {query}\n")
                f.write(f"Number of sources: {len(search_results['texts'])}\n")
                f.write("=" * 80 + "\n\n")
                for i, text in enumerate(search_results['texts'], 1):
                    f.write(f"SOURCE {i}:\n")
                    f.write("-" * 40 + "\n")
                    f.write(text)
                    f.write("\n\n" + "=" * 80 + "\n\n")
            print(f"✓ Original content saved to: {combined_content_file}")
            
            # Save focused content and comparison
            save_focused_content(query, search_results['texts'], focused_texts, "scraped_content")
            
        except Exception as e:
            print(f"✗ Error saving content: {e}")
        
        # Step 6: Generate summary from focused content
        print("Step 6: Generating summary from focused content...")
        summary = summarize(focused_texts, query)
        
        # Step 7: Cache results
        print("Step 7: Caching results...")
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
        scrape_results = scrape_multiple_urls(urls, save_to_files=True, output_dir="scraped_content", max_workers=max_workers)
        
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
        
    def execute_full_pipeline(self, query: str) -> Dict:
        """Execute the full pipeline: classify, search, scrape, and summarize"""
        start_time = time.time()
        
        # Step 1: Validate query
        print(f"\n=== EXECUTING FULL PIPELINE FOR QUERY: '{query}' ===")
        print("Step 1: Classifying query...")
        classifier = get_perplexity_classifier()
        classification_result = classifier.classify_query(query)
        is_valid = classification_result.is_valid
        print(f"Classification result: {is_valid} (Confidence: {classification_result.confidence:.2f}, Intent: {classification_result.intent})")
        
        if not is_valid:
            print("❌ Query rejected by classifier - stopping pipeline")
            return {
                "valid": False,
                "summary": "Query was classified as invalid.",
                "classification_result": classification_result,
                "processing_time": time.time() - start_time
            }
        
        print("✅ Query passed classification - continuing pipeline")
        
        # Step 2: Search for URLs
        print("Step 2: Searching for URLs...")
        search_start = time.time()
        search_result = self.search_only(query)
        urls = search_result.get("urls", [])
        search_time = time.time() - search_start
        print(f"Found {len(urls)} URLs")
        
        if not urls:
            return {
                "valid": True,
                "summary": "No relevant URLs found for the query.",
                "classification_result": classification_result,
                "urls_found": 0,
                "content_scraped": 0,
                "processing_time": time.time() - start_time,
                "search_time": search_time
            }
        
        # Step 3: Scrape content from URLs
        print("Step 3: Scraping content from URLs...")
        scrape_start = time.time()
        
        # Use scrape_multiple_urls for parallel scraping
        texts = []
        successful_scrapes = 0
        scrape_results = scrape_multiple_urls(urls, save_to_files=True, output_dir="scraped_content")
        
        for result in scrape_results:
            if result['success']:
                texts.append(result['content'])
                successful_scrapes += 1
                
        scrape_time = time.time() - scrape_start
        print(f"Successfully scraped {successful_scrapes}/{len(urls)} URLs")
        
        if not texts:
            return {
                "valid": True,
                "summary": "No content was successfully scraped from the found URLs.",
                "classification_result": classification_result,
                "urls_found": len(urls),
                "content_scraped": 0,
                "processing_time": time.time() - start_time,
                "search_time": search_time,
                "scrape_time": scrape_time
            }
        
        # Step 4: Extract focused content from scraped data
        print("Step 4: Extracting focused content...")
        extraction_start = time.time()
        
        # Try Groq first, fallback to TextRank if not available
        extraction_method = "groq" if os.getenv("GROQ_API_KEY") else "textrank"
        print(f"Using extraction method: {extraction_method}")
        
        focused_texts = extract_focused_content(
            query=query,
            texts=texts,
            method=extraction_method,
            sentences_ratio=0.3
        )
        
        extraction_time = time.time() - extraction_start
        print(f"✅ Focused extraction complete - reduced from {len(texts)} to {len(focused_texts)} sources")
        
        # Step 5: Save both original and focused content for comparison
        print("Step 5: Saving content for analysis...")
        try:
            os.makedirs("scraped_content", exist_ok=True)
            
            # Save original combined content
            combined_content_file = "scraped_content/combined_content_for_summarizer.txt"
            with open(combined_content_file, 'w', encoding='utf-8') as f:
                f.write(f"Query: {query}\n")
                f.write(f"Number of sources: {len(texts)}\n")
                f.write("=" * 80 + "\n\n")
                for i, text in enumerate(texts, 1):
                    f.write(f"SOURCE {i}:\n")
                    f.write("-" * 40 + "\n")
                    f.write(text)
                    f.write("\n\n" + "=" * 80 + "\n\n")
            print(f"✓ Original content saved to: {combined_content_file}")
            
            # Save focused content and comparison
            save_focused_content(query, texts, focused_texts, "scraped_content")
            
        except Exception as e:
            print(f"✗ Error saving content: {e}")
        
        # Step 6: Summarize the focused content
        print("Step 6: Summarizing focused content...")
        summarize_start = time.time()
        summary = summarize(focused_texts, query)
        summarization_time = time.time() - summarize_start
        print("✅ Summarization complete")
        
        # Step 7: Cache results
        print("Step 7: Caching results...")
        self._cache_results(query, summary)
        
        print("✅ Full pipeline completed successfully")
        
        return {
            "valid": True,
            "summary": summary,
            "classification_result": classification_result,
            "urls_found": len(urls),
            "content_scraped": successful_scrapes,
            "focused_sources": len(focused_texts),
            "extraction_method": extraction_method,
            "processing_time": time.time() - start_time,
            "search_time": search_time,
            "scrape_time": scrape_time,
            "extraction_time": extraction_time,
            "summarization_time": summarization_time
        }

# Global instance for use in FastAPI endpoints
query_processor = QueryProcessor()