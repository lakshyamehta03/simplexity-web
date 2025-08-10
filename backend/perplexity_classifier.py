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
    Classifies queries as VALID (information-seeking) or INVALID (action commands/nonsensical).

    VALID queries are processed by the AI assistant for research and information retrieval.
    INVALID queries are rejected early to save resources.
    """

    def __init__(self, provider: str = "groq", api_key: str = None):
        self.provider = provider
        self.api_key = api_key or os.getenv(f"{provider.upper()}_API_KEY")
        
        if not self.api_key:
            raise ValueError(f"No API key found for {provider}. Please set {provider.upper()}_API_KEY environment variable or pass api_key parameter.")
        
        self.setup_provider()

        # Optimized prompt template based on research
        self.prompt_template = """You are a query classifier for an AI assistant. Classify queries as VALID (information-seeking) or INVALID (action commands or nonsensical).

VALID queries seek information, knowledge, explanations, or guidance:
- Questions: "What is machine learning?"
- How-to requests: "How to learn Python?"
- Comparisons: "iPhone vs Android"
- Explanations: "Explain quantum computing"
- Research: "Latest AI developments"
- Recommendations: "Best laptops for programming"

INVALID queries are action commands or nonsensical:
- Device control: "Set alarm for 6am"
- Communication: "Call my mom"
- Booking/purchasing: "Book a hotel"
- Personal tasks: "Remind me to buy milk"
- Random text: "hello", "test test"
- Nonsensical: "walk my apples for my dog"

Examples:
Query: "What is the weather today?" → VALID
Query: "Set alarm for 5pm" → INVALID
Query: "How to make bread?" → VALID
Query: "Call John now" → INVALID
Query: "Compare electric vs gas cars" → VALID
Query: "Book flight to Paris" → INVALID

Classify this query: "{query}"

Answer with only: VALID or INVALID"""

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

                # Extract VALID or INVALID from response
                if "VALID" in raw_response and "INVALID" not in raw_response:
                    is_valid = True
                    confidence = 0.9
                    intent = self._determine_intent(query)
                elif "INVALID" in raw_response:
                    is_valid = False
                    confidence = 0.9
                    intent = "INVALID_QUERY"
                else:
                    # Default to INVALID if response is unclear
                    is_valid = False
                    confidence = 0.5
                    intent = "UNCLEAR_RESPONSE"

                inference_time = (time.time() - start_time) * 1000  # Convert to ms

                result = ClassificationResult(
                    is_valid=is_valid,
                    confidence=confidence,
                    intent=intent,
                    reasoning=f"Classified as {'VALID' if is_valid else 'INVALID'} by {self.provider}",
                    inference_time_ms=inference_time
                )

                # Cache result
                if use_cache:
                    self.cache[query] = result

                logger.info(f"Query '{query}' classified as {'VALID' if is_valid else 'INVALID'} "
                           f"(confidence: {confidence:.3f}, intent: {intent}, time: {inference_time:.2f}ms)")

                return result

            except Exception as e:
                logger.error(f"Error during classification: {e}")
                # Fallback: classify as INVALID to be safe
                inference_time = (time.time() - start_time) * 1000
                return ClassificationResult(
                    is_valid=False,
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

# Test function
if __name__ == "__main__":
    # Test queries based on Perplexity-style requirements
    test_queries = [
        # VALID queries (information-seeking)
        "What is machine learning?",
        "How do I learn Python programming?",
        "Compare iPhone vs Android",
        "Explain artificial intelligence",
        "Latest developments in AI",
        "Best restaurants in New York",
        "What are the symptoms of flu?",
        "How does photosynthesis work?",

        # INVALID queries (commands/nonsensical)
        "Set alarm for 6am",
        "Call my mom",
        "Book a hotel in Paris",
        "Send email to John",
        "Play some music",
        "Turn off the lights",
        "Remind me to buy groceries",
        "hello",
        "test",
        "walk my pet; add apples to grocery; set alarm for 5pm",
        "efofjseofijesfo?",
        "blah blah blah"
    ]

    # Initialize classifier
    try:
        classifier = PerplexityStyleQueryClassifier(
            provider="groq",  # Recommended for speed
            api_key=None  # Will use environment variable
        )
    except ValueError as e:
        print(f"❌ Error: {e}")
        print("💡 Please set your API key in the .env file:")
        print("   GROQ_API_KEY=your-groq-api-key-here")
        exit(1)

    print("🚀 PERPLEXITY-STYLE QUERY CLASSIFIER")
    print("=" * 50)
    print("Testing query classification for AI assistant...")
    print()

    # Run batch classification
    results = classifier.batch_classify(test_queries)

    print("📊 CLASSIFICATION RESULTS:")
    print("-" * 30)

    for i, result in enumerate(results, 1):
        status = "✅" if result.is_valid else "❌"
        print(f"{status} Query {i}: {result.is_valid}")
        print(f"   Intent: {result.intent}")
        print(f"   Confidence: {result.confidence:.1f} | Time: {result.inference_time_ms:.1f}ms")
        print()

    # Show summary
    stats = classifier.get_classification_stats()
    print("📈 PERFORMANCE SUMMARY:")
    print("-" * 30)
    print(f"Total queries processed: {stats['total_queries']}")
    print(f"VALID queries: {stats['valid_queries']}")
    print(f"INVALID queries: {stats['invalid_queries']}")
    print(f"Average response time: {stats['average_time_ms']}ms")
    print(f"Validity rate: {stats['validity_rate']:.1%}")

    # Test individual query
    print()
    print("🔍 INDIVIDUAL QUERY TEST:")
    print("-" * 30)
    test_query = "How do neural networks work?"
    is_valid = classifier.is_query_valid(test_query)
    print(f'Query: "{test_query}"')
    print(f"Valid for AI processing: {is_valid}")

    print("\n" + "=" * 50)
    print("Test completed!") 