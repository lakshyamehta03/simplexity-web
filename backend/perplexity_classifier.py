#!/usr/bin/env python3
"""
Perplexity-style query classifier using cloud APIs
Fast and reliable classification for AI assistant queries
"""

import requests
import json
import time
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ClassificationResult:
    """Result of query classification"""
    is_valid: bool
    is_time_sensitive: bool
    confidence: float
    intent: str = "OTHER"
    topic: str = ""
    quality_score: float = 0.5
    reasoning: str = ""
    suggested_improvements: List[str] = None
    inference_time_ms: float = 0.0

    def __post_init__(self):
        if self.suggested_improvements is None:
            self.suggested_improvements = []

class PerplexityStyleQueryClassifier:
    """
    Fast query classifier for a Perplexity-style AI assistant.
    Classifies queries as VALID (information-seeking) or INVALID (action commands/nonsensical)
    AND
    TIME-SENSITIVE (requires up-to-date info) or NOT TIME-SENSITIVE (general knowledge).

    VALID queries are processed by the AI assistant for research and information retrieval.
    INVALID queries are rejected early to save resources.
    
    TIME-SENSITIVE queries require real-time data from the web.
    NOT TIME-SENSITIVE queries can use cached data.
    """

    def __init__(self, provider: str = "groq", api_key: str = None):
        self.provider = provider
        self.api_key = api_key or os.getenv(f"{provider.upper()}_API_KEY")
        
        if not self.api_key:
            raise ValueError(f"No API key found for {provider}. Please set {provider.upper()}_API_KEY environment variable or pass api_key parameter.")
        
        self.setup_provider()

        # Optimized prompt template based on research
#         self.prompt_template = """You are a query classifier for an AI assistant. Classify queries as VALID (information-seeking) or INVALID (action commands or nonsensical).

# VALID queries seek information, knowledge, explanations, or guidance:
# - Questions: "What is machine learning?"
# - How-to requests: "How to learn Python?"
# - Comparisons: "iPhone vs Android"
# - Explanations: "Explain quantum computing"
# - Research: "Latest AI developments"
# - Recommendations: "Best laptops for programming"

# INVALID queries are action commands or nonsensical:
# - Device control: "Set alarm for 6am"
# - Communication: "Call my mom"
# - Booking/purchasing: "Book a hotel"
# - Personal tasks: "Remind me to buy milk"
# - Random text: "hello", "test test"
# - Nonsensical: "walk my apples for my dog"

# Examples:
# Query: "What is the weather today?" → VALID
# Query: "Set alarm for 5pm" → INVALID
# Query: "How to make bread?" → VALID
# Query: "Call John now" → INVALID
# Query: "Compare electric vs gas cars" → VALID
# Query: "Book flight to Paris" → INVALID

# Classify this query: "{query}"

# Answer with only: VALID or INVALID"""



        # Time Sensitivity + Validity  Classifier
        self.prompt_template = """You are a query classifier for an AI assistant. For each user query, you must:
1. Classify as VALID (seeking information, knowledge, explanations, or guidance) or INVALID (action command, agent control, nonsense).
2. Classify as TIME-SENSITIVE (needs up-to-date info, e.g. 'today', 'current', 'latest', dates, breaking news) or NOT TIME-SENSITIVE (general knowledge, facts, advice, history, definitions).

Respond with:
VALIDITY: (VALID or INVALID)
TIME_SENSITIVITY: (TIME-SENSITIVE or NOT TIME-SENSITIVE)

Examples:
---
Query: "Compare electric cars vs gas cars"
VALIDITY: VALID
TIME_SENSITIVITY: NOT TIME-SENSITIVE
REASON: General factual info.

Query: "What is the weather in Paris today?"
VALIDITY: VALID
TIME_SENSITIVITY: TIME-SENSITIVE
REASON: Requires up-to-date weather data.

Query: "Book me a flight"
VALIDITY: INVALID
TIME_SENSITIVITY: TIME-SENSITIVE
REASON: An action command and also requires real-time info.

---
Classify this query.
Query: "{query}"
"""

        # Cache for results
        self.cache = {}

    def setup_provider(self):
        """Setup API configuration for different providers"""
        if self.provider == "groq":
            self.api_url = "https://api.groq.com/openai/v1/chat/completions"
            self.model = "llama-3.1-8b-instant"  # Fastest model
            self.headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        elif self.provider == "together":
            self.api_url = "https://api.together.xyz/v1/chat/completions"
            self.model = "meta-llama/Llama-3.2-3B-Instruct-Turbo"  # Fast and small
            self.headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        elif self.provider == "openai":
            self.api_url = "https://api.openai.com/v1/chat/completions"
            self.model = "gpt-3.5-turbo"  # Fast and reliable
            self.headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    def classify_query(self, query: str, use_cache: bool = True) -> ClassificationResult:
        """
        Classify a single query as VALID or INVALID

        Args:
            query: The query to classify
            use_cache: Whether to use cached results

        Returns:
            ClassificationResult object
        """
        if not query or not query.strip():
            return ClassificationResult(
                is_valid=False,
                is_time_sensitive=False,
                confidence=1.0,
                intent="EMPTY_QUERY",
                reasoning="Query is empty or contains only whitespace"
            )

        # Check cache
        if use_cache and query in self.cache:
            return self.cache[query]

        start_time = time.time()

        # Create the prompt
        prompt = self.prompt_template.format(query=query)

        if self.provider in ["groq", "together", "openai"]:
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.1,  # Low temperature for consistent classification
                "max_tokens": 5,     # We only need "VALID" or "INVALID"
                "stream": False
            }

            try:
                response = requests.post(self.api_url, headers=self.headers, json=payload, timeout=10)
                response.raise_for_status()

                result = response.json()
                raw_response = result['choices'][0]['message']['content'].strip().upper()

                # Parse both validity and time sensitivity from response
                is_valid = False
                is_time_sensitive = False
                confidence = 0.9
                
                # Parse validity
                if "VALIDITY: VALID" in raw_response or ("VALID" in raw_response and "INVALID" not in raw_response):
                    is_valid = True
                    intent = self._determine_intent(query)
                elif "VALIDITY: INVALID" in raw_response or "INVALID" in raw_response:
                    is_valid = False
                    intent = "INVALID_QUERY"
                else:
                    # Default to INVALID if response is unclear
                    is_valid = False
                    confidence = 0.5
                    intent = "UNCLEAR_RESPONSE"
                
                # Parse time sensitivity
                if "TIME_SENSITIVITY: TIME-SENSITIVE" in raw_response or "TIME-SENSITIVE" in raw_response:
                    is_time_sensitive = True
                elif "TIME_SENSITIVITY: NOT TIME-SENSITIVE" in raw_response or "NOT TIME-SENSITIVE" in raw_response:
                    is_time_sensitive = False
                else:
                    # Default based on query content
                    is_time_sensitive = self._is_query_time_sensitive(query)

                inference_time = (time.time() - start_time) * 1000  # Convert to ms

                result = ClassificationResult(
                    is_valid=is_valid,
                    is_time_sensitive=is_time_sensitive,
                    confidence=confidence,
                    intent=intent,
                    reasoning=f"Classified as {'VALID' if is_valid else 'INVALID'} and {'TIME-SENSITIVE' if is_time_sensitive else 'NOT TIME-SENSITIVE'} by {self.provider}",
                    inference_time_ms=inference_time
                )

                # Cache result
                if use_cache:
                    self.cache[query] = result

                logger.info(f"Query '{query}' classified as {'VALID' if is_valid else 'INVALID'} "
                           f"and {'TIME-SENSITIVE' if is_time_sensitive else 'NOT TIME-SENSITIVE'} "
                           f"(confidence: {confidence:.3f}, intent: {intent}, time: {inference_time:.2f}ms)")

                return result

            except Exception as e:
                logger.error(f"Error during classification: {e}")
                # Fallback: classify as INVALID to be safe
                inference_time = (time.time() - start_time) * 1000
                return ClassificationResult(
                    is_valid=False,
                    is_time_sensitive=False,
                    confidence=0.0,
                    intent="ERROR",
                    reasoning=f"Classification error: {str(e)}",
                    inference_time_ms=inference_time
                )

    def _determine_intent(self, query: str) -> str:
        """Determine the intent of a valid query"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['how to', 'how do', 'steps to', 'guide']):
            return "HOW_TO"
        elif any(word in query_lower for word in ['compare', 'vs', 'versus', 'difference']):
            return "COMPARISON"
        elif any(word in query_lower for word in ['what is', 'define', 'explain', 'meaning']):
            return "DEFINITION"
        elif any(word in query_lower for word in ['latest', 'news', 'recent', 'current']):
            return "NEWS_CURRENT_EVENTS"
        elif any(word in query_lower for word in ['best', 'recommend', 'top', 'suggest']):
            return "RECOMMENDATION"
        elif any(word in query_lower for word in ['statistics', 'data', 'numbers', 'percentage']):
            return "STATISTICS_DATA"
        elif '?' in query:
            return "FACTUAL_QUESTION"
        else:
            return "OTHER"
    
    def _is_query_time_sensitive(self, query: str) -> bool:
        """Determine if a query is time-sensitive based on keywords"""
        query_lower = query.lower()
        
        # Time-sensitive keywords
        time_sensitive_keywords = [
            'today', 'tomorrow', 'yesterday', 'now', 'current', 'latest', 'recent',
            'breaking', 'live', 'upcoming', 'this week', 'this month', 'this year',
            '2024', '2025', '2023', '2022', '2021', '2020', '2019', '2018', '2017',
            'weather', 'stock', 'price', 'market', 'election', 'news', 'update',
            'score', 'result', 'outcome', 'deadline', 'due date', 'schedule'
        ]
        
        # Check for time-sensitive keywords
        for keyword in time_sensitive_keywords:
            if keyword in query_lower:
                return True
        
        # Check for date patterns (YYYY, MM/DD, etc.)
        import re
        date_patterns = [
            r'\b\d{4}\b',  # Year
            r'\b\d{1,2}/\d{1,2}\b',  # MM/DD or M/D
            r'\b\d{1,2}-\d{1,2}\b',  # MM-DD or M-D
            r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\b',
            r'\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\b'
        ]
        
        for pattern in date_patterns:
            if re.search(pattern, query_lower):
                return True
        
        return False

    def batch_classify(self, queries: List[str]) -> List[ClassificationResult]:
        """Classify multiple queries efficiently"""
        results = []
        total_start = time.time()

        for i, query in enumerate(queries):
            try:
                result = self.classify_query(query)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to classify query '{query}': {e}")
                results.append(ClassificationResult(
                    is_valid=False,
                    is_time_sensitive=False,
                    confidence=0.0,
                    intent="ERROR",
                    reasoning=f"Classification failed: {str(e)}"
                ))

            # Small delay to avoid rate limiting
            if i < len(queries) - 1:
                time.sleep(0.1)

        return results

    def get_classification_stats(self) -> Dict:
        """Get statistics about classifications performed"""
        if not self.cache:
            return {"total_queries": 0, "cache_hits": 0}

        total_queries = len(self.cache)
        valid_queries = sum(1 for result in self.cache.values() if result.is_valid)
        invalid_queries = total_queries - valid_queries

        intent_counts = {}
        for result in self.cache.values():
            intent_counts[result.intent] = intent_counts.get(result.intent, 0) + 1

        avg_time = sum(r.inference_time_ms for r in self.cache.values()) / total_queries if total_queries > 0 else 0

        return {
            "total_queries": total_queries,
            "valid_queries": valid_queries,
            "invalid_queries": invalid_queries,
            "validity_rate": valid_queries / total_queries if total_queries > 0 else 0,
            "intent_distribution": intent_counts,
            "average_confidence": sum(r.confidence for r in self.cache.values()) / total_queries if total_queries > 0 else 0,
            "average_time_ms": round(avg_time, 2)
        }

    def is_query_valid(self, query: str) -> bool:
        """Simple boolean check for query validity"""
        result = self.classify_query(query)
        return result.is_valid

# Global classifier instance
_perplexity_classifier_instance = None

def get_perplexity_classifier(provider: str = "groq") -> PerplexityStyleQueryClassifier:
    """
    Get or create a global Perplexity-style classifier instance
    
    Args:
        provider: API provider to use (groq, together, openai)
        
    Returns:
        PerplexityStyleQueryClassifier instance
    """
    global _perplexity_classifier_instance
    if _perplexity_classifier_instance is None:
        _perplexity_classifier_instance = PerplexityStyleQueryClassifier(provider=provider)
    return _perplexity_classifier_instance

def classify_query_perplexity(query: str) -> ClassificationResult:
    """
    Classify a query using Perplexity-style classifier
    
    Args:
        query: The query to classify
        
    Returns:
        ClassificationResult object
    """
    classifier = get_perplexity_classifier()
    return classifier.classify_query(query)