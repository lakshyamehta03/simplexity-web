from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from perplexity_classifier import get_perplexity_classifier
from embeddings import get_embedding
from db import query_db, add_to_db, clear_cache, get_cache_stats, list_cached_queries, debug_cache_content
from query_processor import query_processor
from content_scraper import scrape_content, scrape_multiple_urls
from summarizer import summarize
from typing import List, Optional, Dict, Any
import time

app = FastAPI()

# Add CORS middleware with wildcard origin for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=False,  # Must be False when allow_origins=["*"]
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    valid: bool
    summary: str = None
    from_cache: bool = False
    urls_found: int = 0
    content_scraped: int = 0
    processing_time: float = 0.0
    search_time: float = 0.0
    scrape_time: float = 0.0
    cache_similarity: float = 0.0

class ClassifyRequest(BaseModel):
    query: str
    provider: str = "groq"
    use_cache: bool = True

class ClassifyResponse(BaseModel):
    is_valid: bool
    confidence: float
    intent: str
    topic: str
    quality_score: float
    reasoning: str
    suggested_improvements: List[str]

class FullPipelineResponse(BaseModel):
    valid: bool
    summary: str = None
    classification_result: ClassifyResponse = None
    urls_found: int = 0
    content_scraped: int = 0
    processing_time: float = 0.0
    search_time: float = 0.0
    scrape_time: float = 0.0
    summarization_time: float = 0.0

class ScrapeRequest(BaseModel):
    urls: List[str]

@app.get("/")
def root():
    """Root endpoint with API information"""
    return {
        "message": "Ripplica Query Core API",
        "version": "1.0.0",
        "endpoints": {
            "POST /query": "Process a query through the complete pipeline",
            "POST /search-only": "Search DuckDuckGo for URLs only",
            "POST /scrape-only": "Scrape content from provided URLs only",
            "POST /classify": "Classify a query with detailed analysis",
            "POST /full-pipeline": "Execute full pipeline: classify, search, scrape, and summarize",
            "GET /cache/stats": "Get cache statistics",
            "POST /cache/clear": "Clear the cache",
            "GET /cache/debug": "Debug cache contents",
            "GET /health": "Health check"
        }
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "message": "Backend is running"}

@app.get("/cache/stats")
def get_cache_statistics():
    """Get cache statistics"""
    count = get_cache_stats()
    queries = list_cached_queries()
    return {
        "cache_count": count,
        "cached_queries": queries
    }

@app.post("/cache/clear")
def clear_cache_endpoint():
    """Clear the cache"""
    clear_cache()
    return {"message": "Cache cleared successfully"}

@app.get("/cache/debug")
def debug_cache():
    """Debug cache contents"""
    debug_cache_content()
    return {"message": "Cache debug info printed to console"}

@app.post("/classify", response_model=ClassifyResponse)
def classify_query(req: ClassifyRequest):
    """Classify a query using Perplexity-style classifier"""
    try:
        classifier = get_perplexity_classifier(req.provider)
        result = classifier.classify_query(req.query, use_cache=req.use_cache)
        
        return ClassifyResponse(
            is_valid=result.is_valid,
            confidence=result.confidence,
            intent=result.intent,
            topic=result.topic,
            quality_score=result.quality_score,
            reasoning=result.reasoning,
            suggested_improvements=result.suggested_improvements
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Classification failed: {str(e)}")

@app.post("/query", response_model=QueryResponse)
def process_query(req: QueryRequest):
    """Main query endpoint using the modular QueryProcessor"""
    result = query_processor.process_query(req.query)
    
    return QueryResponse(
        valid=result["valid"],
        summary=result.get("summary"),
        from_cache=result.get("from_cache", False),
        urls_found=result.get("urls_found", 0),
        content_scraped=result.get("content_scraped", 0),
        processing_time=result.get("processing_time", 0.0),
        search_time=result.get("search_time", 0.0),
        scrape_time=result.get("scrape_time", 0.0),
        cache_similarity=result.get("cache_similarity", 0.0)
    )

# For testing the search method
@app.post("/search-only")
def search_only(req: QueryRequest):
    """Endpoint to test search functionality only"""
    result = query_processor.search_only(req.query)
    return result

# For testing the scrape method
@app.post("/scrape-only")
def scrape_only(req: ScrapeRequest):
    """Endpoint to test scraping functionality only"""
    result = query_processor.scrape_only(req.urls)
    return result

@app.post("/full-pipeline", response_model=FullPipelineResponse)
def execute_full_pipeline(req: QueryRequest):
    """Execute the full pipeline: classify, search, scrape, and summarize"""
    try:
        # Use the query_processor's execute_full_pipeline method
        result = query_processor.execute_full_pipeline(req.query)
        
        # Convert the classification_result to ClassifyResponse
        classification_result = result.get("classification_result")
        if classification_result:
            classify_response = ClassifyResponse(
                is_valid=classification_result.is_valid,
                confidence=classification_result.confidence,
                intent=classification_result.intent,
                topic=classification_result.topic,
                quality_score=classification_result.quality_score,
                reasoning=classification_result.reasoning,
                suggested_improvements=classification_result.suggested_improvements
            )
        else:
            classify_response = None
        
        # Return the full pipeline response
        return FullPipelineResponse(
            valid=result.get("valid", False),
            summary=result.get("summary", ""),
            classification_result=classify_response,
            urls_found=result.get("urls_found", 0),
            content_scraped=result.get("content_scraped", 0),
            processing_time=result.get("processing_time", 0.0),
            search_time=result.get("search_time", 0.0),
            scrape_time=result.get("scrape_time", 0.0),
            summarization_time=result.get("summarization_time", 0.0)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Full pipeline execution failed: {str(e)}")