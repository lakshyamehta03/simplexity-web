from fastapi import FastAPI, HTTPException
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from perplexity_classifier import get_perplexity_classifier
from embeddings import get_embedding
from db import query_db, add_to_db, clear_cache, get_cache_stats, list_cached_queries, debug_cache_content
from query_processor import query_processor
from content_scraper import scrape_content, scrape_multiple_urls
from summarizer import summarize
from typing import Optional, Dict, Any, List
import time
import numpy as np
import asyncio
import logging
from datetime import datetime

# Configure logging for WebSocket operations
logging.basicConfig(level=logging.INFO)
ws_logger = logging.getLogger("websocket")
ws_logger.setLevel(logging.INFO)

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
    is_valid: bool
    is_time_sensitive: bool
    summary: Optional[str] = None
    from_cache: bool = False
    cached_query: Optional[str] = None
    urls_found: int = 0
    content_scraped: int = 0
    scraped_urls: List[str] = []
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
    is_time_sensitive: bool
    confidence: float
    intent: str
    topic: str
    quality_score: float
    reasoning: str
    suggested_improvements: List[str]

class FullPipelineResponse(BaseModel):
    valid: bool
    is_valid: bool
    is_time_sensitive: bool
    summary: Optional[str] = None
    classification_result: Optional[ClassifyResponse] = None
    urls_found: int = 0
    content_scraped: int = 0
    processing_time: float = 0.0
    search_time: float = 0.0
    scrape_time: float = 0.0
    summarization_time: float = 0.0

class ScrapeRequest(BaseModel):
    urls: List[str]

class CacheTestRequest(BaseModel):
    query: str
    threshold: float = 0.8

class CacheAddRequest(BaseModel):
    query: str
    summary: str

class SimilarityCheckRequest(BaseModel):
    query: str
    threshold: float = 0.7


class WSManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        ws_logger.info("WSManager initialized")

    async def connect(self, ws_id: str, websocket: WebSocket):
        try:
            await websocket.accept()
            self.active_connections[ws_id] = websocket
            ws_logger.info(f"WebSocket connected successfully - ws_id: {ws_id}, total_connections: {len(self.active_connections)}")
        except Exception as e:
            ws_logger.error(f"Failed to connect WebSocket - ws_id: {ws_id}, error: {e}")
            raise

    def disconnect(self, ws_id: str):
        if ws_id in self.active_connections:
            self.active_connections.pop(ws_id, None)
            ws_logger.info(f"WebSocket disconnected - ws_id: {ws_id}, remaining_connections: {len(self.active_connections)}")
        else:
            ws_logger.warning(f"Attempted to disconnect non-existent WebSocket - ws_id: {ws_id}")

    async def send_json(self, ws_id: str, message: Dict[str, Any]):
        websocket = self.active_connections.get(ws_id)
        if websocket:
            try:
                await websocket.send_json(message)
                ws_logger.debug(f"Message sent to WebSocket - ws_id: {ws_id}, step: {message.get('step', 'unknown')}")
            except Exception as e:
                ws_logger.error(f"Failed to send message to WebSocket - ws_id: {ws_id}, error: {e}")
                # Remove the connection if it's broken
                self.disconnect(ws_id)
        else:
            ws_logger.warning(f"Attempted to send message to non-existent WebSocket - ws_id: {ws_id}")


ws_manager = WSManager()

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
            "POST /cache/check": "Check if a specific query would hit the cache",
            "POST /cache/add": "Add a query and summary to cache manually",
            "POST /cache/similar": "Find similar queries in cache",
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

@app.post("/cache/check")
def check_cache(req: CacheTestRequest):
    """Check if a specific query would hit the cache"""
    try:
        from query_processor import QueryProcessor
        processor = QueryProcessor(cache_threshold=req.threshold)
        cache_result = processor._check_cache(req.query)
        
        return {
            "query": req.query,
            "threshold": req.threshold,
            "hit": cache_result['hit'],
            "similarity": cache_result.get('similarity', 0),
            "cached_query": cache_result.get('cached_query', None)
        }
    except Exception as e:
        return {"error": f"Cache check failed: {str(e)}"}

@app.post("/cache/add")
def add_to_cache(req: CacheAddRequest):
    """Add a query and summary to cache manually"""
    try:
        from embeddings import get_embedding
        from db import add_to_db
        
        # Generate embedding for the query
        embedding = get_embedding(req.query)
        
        # Add to cache
        doc_id = add_to_db(embedding, req.summary, metadata={"query": req.query})
        
        if doc_id:
            return {
                "success": True,
                "message": "Query added to cache successfully",
                "doc_id": doc_id,
                "query": req.query,
                "summary_length": len(req.summary)
            }
        else:
            return {"success": False, "error": "Failed to add query to cache"}
            
    except Exception as e:
        return {"success": False, "error": f"Failed to add to cache: {str(e)}"}

@app.post("/cache/similar")
def find_similar_queries(req: SimilarityCheckRequest):
    """Find similar queries in cache with detailed similarity scores"""
    try:
        from embeddings import get_embedding
        from db import collection
        import numpy as np
        
        # Generate embedding for the query
        embedding = get_embedding(req.query)
        
        # Get all cached queries
        all_results = collection.get()
        
        if not all_results['ids']:
            return {
                "query": req.query,
                "threshold": req.threshold,
                "similar_queries": [],
                "message": "Cache is empty"
            }
        
        similar_queries = []
        
        # Calculate similarity with each cached query
        for i, (doc_id, cached_query, cached_summary) in enumerate(zip(
            all_results['ids'],
            [meta.get('query', 'Unknown') for meta in all_results['metadatas']],
            all_results['documents']
        )):
            # Get embedding for cached query
            cached_embedding = get_embedding(cached_query)
            
            # Calculate cosine similarity
            similarity = cosine_similarity(embedding, cached_embedding)
            
            if similarity >= req.threshold:
                similar_queries.append({
                    "doc_id": doc_id,
                    "cached_query": cached_query,
                    "similarity": round(similarity, 3),
                    "summary_preview": cached_summary[:100] + "..." if len(cached_summary) > 100 else cached_summary
                })
        
        # Sort by similarity (highest first)
        similar_queries.sort(key=lambda x: x['similarity'], reverse=True)
        
        return {
            "query": req.query,
            "threshold": req.threshold,
            "total_cached_queries": len(all_results['ids']),
            "similar_queries": similar_queries,
            "similar_count": len(similar_queries)
        }
        
    except Exception as e:
        return {"error": f"Failed to find similar queries: {str(e)}"}

def cosine_similarity(embedding1, embedding2):
    """Calculate cosine similarity between two embeddings"""
    try:
        # Normalize embeddings
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        # Calculate cosine similarity
        similarity = np.dot(embedding1, embedding2) / (norm1 * norm2)
        return float(similarity)
        
    except Exception as e:
        print(f"Error calculating similarity: {e}")
        return 0.0

@app.post("/classify", response_model=ClassifyResponse)
def classify_query(req: ClassifyRequest):
    """Classify a query using Perplexity-style classifier"""
    try:
        classifier = get_perplexity_classifier(req.provider)
        result = classifier.classify_query(req.query, use_cache=req.use_cache)
        
        return ClassifyResponse(
            is_valid=result.is_valid,
            is_time_sensitive=result.is_time_sensitive,
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
async def process_query(req: QueryRequest):
    """Main query endpoint using the modular QueryProcessor"""
    try:
        result = await query_processor.process_query(req.query)
        scraped_urls = result.get("scraped_urls", [])
        
        # Debug logging for scraped_urls
        logging.info(f"DEBUG: scraped_urls count: {len(scraped_urls)}")
        logging.info(f"DEBUG: scraped_urls content: {scraped_urls}")
        
        response = QueryResponse(
            valid=result["valid"],
            is_valid=result.get("is_valid", result["valid"]),
            is_time_sensitive=result.get("is_time_sensitive", False),
            summary=result.get("summary"),
            from_cache=result.get("from_cache", False),
            cached_query=result.get("cached_query"),
            urls_found=result.get("urls_found", 0),
            content_scraped=result.get("content_scraped", 0),
            scraped_urls=scraped_urls,
            processing_time=result.get("processing_time", 0.0),
            search_time=result.get("search_time", 0.0),
            scrape_time=result.get("scrape_time", 0.0),
            cache_similarity=result.get("cache_similarity", 0.0)
        )
        
        logging.info(f"DEBUG: Response scraped_urls: {response.scraped_urls}")
        return response
    except Exception as e:
        logging.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

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
                is_time_sensitive=classification_result.is_time_sensitive,
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
            is_valid=result.get("is_valid", result.get("valid", False)),
            is_time_sensitive=result.get("is_time_sensitive", False),
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


@app.websocket("/ws/status/{ws_id}")
async def websocket_status(websocket: WebSocket, ws_id: str):
    """WebSocket to stream realtime status updates for a query"""
    connection_start = datetime.now()
    ws_logger.info(f"WebSocket connection attempt - ws_id: {ws_id}, timestamp: {connection_start}")
    
    try:
        await ws_manager.connect(ws_id, websocket)
        ws_logger.info(f"WebSocket connection established - ws_id: {ws_id}")
        
        # Send initial connection confirmation
        await websocket.send_json({"step": "connected", "ws_id": ws_id, "timestamp": connection_start.isoformat()})
        ws_logger.debug(f"Initial connection message sent - ws_id: {ws_id}")
        
        ping_count = 0
        while True:
            # Keep the connection alive by awaiting client pings/messages
            # Use a timeout to prevent hanging indefinitely
            try:
                message = await asyncio.wait_for(websocket.receive_text(), timeout=1.0)
                ws_logger.debug(f"Received message from client - ws_id: {ws_id}, message: {message}")
            except asyncio.TimeoutError:
                # Send a ping to keep connection alive
                ping_count += 1
                ping_message = {"step": "ping", "count": ping_count, "timestamp": datetime.now().isoformat()}
                await websocket.send_json(ping_message)
                ws_logger.debug(f"Ping sent - ws_id: {ws_id}, count: {ping_count}")
                
    except WebSocketDisconnect:
        connection_duration = (datetime.now() - connection_start).total_seconds()
        ws_logger.info(f"WebSocket disconnected normally - ws_id: {ws_id}, duration: {connection_duration:.2f}s")
        ws_manager.disconnect(ws_id)
    except Exception as e:
        connection_duration = (datetime.now() - connection_start).total_seconds()
        ws_logger.error(f"WebSocket error - ws_id: {ws_id}, duration: {connection_duration:.2f}s, error: {e}")
        ws_manager.disconnect(ws_id)


@app.post("/query/stream/{ws_id}", response_model=QueryResponse)
async def process_query_stream(ws_id: str, req: QueryRequest):
    """Process a query and stream status updates over websocket if connected"""
    query_start = datetime.now()
    ws_logger.info(f"Starting streaming query processing - ws_id: {ws_id}, query: '{req.query[:100]}...', timestamp: {query_start}")
    
    async def emitter(step: str, data: Dict[str, Any]):
        try:
            message = {"step": step, "timestamp": datetime.now().isoformat(), **data}
            await ws_manager.send_json(ws_id, message)
            ws_logger.info(f"Pipeline step update sent - ws_id: {ws_id}, step: {step}, data_keys: {list(data.keys())}")
        except Exception as e:
            ws_logger.error(f"Failed to emit pipeline step update - ws_id: {ws_id}, step: {step}, error: {e}")

    # Direct async callback for real-time status updates
    async def async_callback(step: str, data: Dict[str, Any]):
        ws_logger.debug(f"Async callback triggered - ws_id: {ws_id}, step: {step}")
        try:
            await emitter(step, data)
            ws_logger.debug(f"Pipeline step emitted immediately - ws_id: {ws_id}, step: {step}")
        except Exception as e:
            ws_logger.error(f"Error in async_callback - ws_id: {ws_id}, step: {step}, error: {e}")

    result = await query_processor.process_query(req.query, status_callback=async_callback)
    
    query_duration = (datetime.now() - query_start).total_seconds()
    ws_logger.info(f"Streaming query processing completed - ws_id: {ws_id}, duration: {query_duration:.2f}s, valid: {result['valid']}, from_cache: {result.get('from_cache', False)}")
    
    scraped_urls = result.get("scraped_urls", [])
    
    # Debug logging for streaming endpoint
    ws_logger.info(f"DEBUG: Streaming endpoint scraped_urls count: {len(scraped_urls)}")
    ws_logger.info(f"DEBUG: Streaming endpoint scraped_urls: {scraped_urls}")
    
    return QueryResponse(
        valid=result["valid"],
        is_valid=result.get("is_valid", result["valid"]),
        is_time_sensitive=result.get("is_time_sensitive", False),
        summary=result.get("summary"),
        from_cache=result.get("from_cache", False),
        cached_query=result.get("cached_query"),
        urls_found=result.get("urls_found", 0),
        content_scraped=result.get("content_scraped", 0),
        scraped_urls=scraped_urls,
        processing_time=result.get("processing_time", 0.0),
        search_time=result.get("search_time", 0.0),
        scrape_time=result.get("scrape_time", 0.0),
        cache_similarity=result.get("cache_similarity", 0.0)
    )