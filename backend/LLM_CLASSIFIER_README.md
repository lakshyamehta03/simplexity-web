# LLM Classifier for Ripplica AI

## Overview

This LLM-based classifier replaces the previous sentence transformer approach with a more sophisticated classification system using free, open-source language models via Ollama. The classifier provides detailed analysis including intent detection, quality scoring, and reasoning.

## Features

- **Multi-model Support**: Works with Llama 2, Mistral, Code Llama, Phi-2, and Gemma models
- **Advanced Classification**: Validates queries, detects intent, and assesses quality
- **Detailed Analysis**: Provides reasoning and improvement suggestions
- **Caching**: Built-in caching for performance optimization
- **Fallback System**: Robust fallback to heuristics if LLM fails
- **Batch Processing**: Efficient classification of multiple queries

## Quick Start

### 1. Install Ollama

**Windows:**
```bash
# Download from https://ollama.ai/download
# Run the installer and restart your terminal
```

**macOS/Linux:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

### 2. Setup the Classifier

```bash
cd backend
python setup_ollama.py
```

This script will:
- Check if Ollama is installed
- Start the Ollama service
- Download the default model (llama2)
- Test the classifier

### 3. Basic Usage

```python
from llm_classifier import LLMClassifier, classify_query_advanced

# Simple classification
classifier = LLMClassifier()
result = classifier.classify_query("What is machine learning?")

print(f"Valid: {result.is_valid}")
print(f"Confidence: {result.confidence}")
print(f"Intent: {result.intent}")
print(f"Quality Score: {result.quality_score}")
print(f"Reasoning: {result.reasoning}")

# Advanced classification with detailed results
result = classify_query_advanced("How to cook pasta?")
print(result)
```

## Available Models

| Model | Size | Performance | Use Case |
|-------|------|-------------|----------|
| `llama2` | 4GB | Balanced | General purpose |
| `llama2:13b` | 7GB | Accurate | High accuracy |
| `mistral` | 4GB | Fast | Fast classification |
| `codellama` | 4GB | Balanced | Technical queries |
| `phi2` | 2GB | Fast | Lightweight |
| `gemma2:2b` | 1.5GB | Very Fast | Very fast classification |

## Configuration

### Model Selection

```python
from llm_config import get_recommended_model, list_available_models

# Get recommended model for your use case
model = get_recommended_model("fast")  # Returns "mistral"

# List all available models
models = list_available_models()
for name, config in models.items():
    print(f"{name}: {config.description}")
```

### Custom Configuration

```python
classifier = LLMClassifier(
    model_name="mistral",
    ollama_url="http://localhost:11434"
)
```

## API Reference

### LLMClassifier Class

#### `__init__(model_name="llama2", ollama_url="http://localhost:11434")`
Initialize the classifier with specified model and Ollama server URL.

#### `classify_query(query: str, use_cache: bool = True) -> ClassificationResult`
Classify a single query and return detailed results.

#### `batch_classify(queries: List[str]) -> List[ClassificationResult]`
Classify multiple queries efficiently.

#### `get_classification_stats() -> Dict`
Get statistics about performed classifications.

### ClassificationResult

```python
@dataclass
class ClassificationResult:
    is_valid: bool                    # Whether the query is valid
    confidence: float                 # Classification confidence (0.0-1.0)
    intent: str                       # Query intent category
    topic: str                        # Main subject area
    quality_score: float              # Overall quality score (0.0-1.0)
    reasoning: str                    # Explanation of classification
    suggested_improvements: List[str] # Improvement suggestions
```

## Intent Categories

- **FACTUAL_QUESTION**: Seeking specific facts or information
- **HOW_TO**: Requesting instructions or tutorials
- **COMPARISON**: Asking to compare options or concepts
- **DEFINITION**: Seeking explanation of a term or concept
- **NEWS_CURRENT_EVENTS**: Asking about recent events or news
- **RESEARCH**: Requesting in-depth analysis or research
- **RECOMMENDATION**: Asking for suggestions or recommendations
- **STATISTICS_DATA**: Requesting numbers, data, or statistics
- **OPINION**: Asking for subjective views or opinions
- **OTHER**: Doesn't fit other categories

## Integration with Existing Code

### Replace Old Classifier

```python
# Old way
from classifier import is_valid_query
result = is_valid_query("What is AI?")

# New way
from llm_classifier import is_valid_query, classify_query_advanced
result = is_valid_query("What is AI?")  # Backward compatible
detailed_result = classify_query_advanced("What is AI?")  # New detailed analysis
```

### Update Main Application

```python
from llm_classifier import get_classifier

classifier = get_classifier("mistral")  # Use faster model for production

def process_query(query: str):
    # Classify the query
    classification = classifier.classify_query(query)
    
    if not classification.is_valid:
        return {
            "error": "Invalid query",
            "reasoning": classification.reasoning,
            "suggestions": classification.suggested_improvements
        }
    
    # Process valid query
    return {
        "query": query,
        "intent": classification.intent,
        "quality_score": classification.quality_score,
        "confidence": classification.confidence
    }
```

## Performance Optimization

### Caching

The classifier automatically caches results for better performance:

```python
# Enable/disable caching
result = classifier.classify_query("What is AI?", use_cache=True)
```

### Batch Processing

For multiple queries, use batch processing:

```python
queries = ["What is AI?", "How to cook pasta?", "Latest news about climate change"]
results = classifier.batch_classify(queries)
```

### Model Selection

Choose the right model for your use case:

```python
# For speed
classifier = LLMClassifier("gemma2:2b")

# For accuracy
classifier = LLMClassifier("llama2:13b")

# For technical queries
classifier = LLMClassifier("codellama")
```

## Troubleshooting

### Ollama Not Running

```bash
# Start Ollama service
ollama serve

# Check if it's running
curl http://localhost:11434/api/tags
```

### Model Not Found

```bash
# List available models
ollama list

# Download a specific model
ollama pull llama2
```

### Performance Issues

1. **Use a smaller model**: Try `gemma2:2b` or `phi2`
2. **Enable caching**: Set `use_cache=True`
3. **Reduce temperature**: Lower temperature for faster, more consistent results
4. **Use batch processing**: For multiple queries

### Memory Issues

1. **Use smaller models**: `gemma2:2b` (1.5GB) or `phi2` (2GB)
2. **Close unused models**: `ollama rm <model_name>`
3. **Monitor memory usage**: Check system resources

## Testing

### Run Tests

```bash
cd backend
python -m pytest tests/test_llm_classifier.py -v
```

### Manual Testing

```python
from llm_classifier import LLMClassifier

classifier = LLMClassifier()

test_queries = [
    "What is machine learning?",
    "Set alarm for 6am",
    "How to cook pasta?",
    "hello",
    "Latest news about AI",
    "Book a flight to Paris"
]

for query in test_queries:
    result = classifier.classify_query(query)
    print(f"Query: {query}")
    print(f"Valid: {result.is_valid}, Confidence: {result.confidence:.3f}")
    print(f"Intent: {result.intent}, Quality: {result.quality_score:.3f}")
    print(f"Reasoning: {result.reasoning}")
    print("-" * 50)
```

## Monitoring and Analytics

### Get Statistics

```python
stats = classifier.get_classification_stats()
print(f"Total queries: {stats['total_queries']}")
print(f"Validity rate: {stats['validity_rate']:.2%}")
print(f"Average confidence: {stats['average_confidence']:.3f}")
print(f"Intent distribution: {stats['intent_distribution']}")
```

### Logging

The classifier includes comprehensive logging:

```python
import logging
logging.basicConfig(level=logging.INFO)

# Now all classification activities will be logged
classifier = LLMClassifier()
result = classifier.classify_query("What is AI?")
```

## Migration from Old Classifier

1. **Install Ollama**: Follow the setup instructions above
2. **Update imports**: Replace `from classifier import is_valid_query` with `from llm_classifier import is_valid_query`
3. **Test thoroughly**: Run the test suite and manual tests
4. **Monitor performance**: Check response times and accuracy
5. **Gradual rollout**: Deploy to a subset of users first

## Future Enhancements

- **Fine-tuning**: Custom model training for specific domains
- **Multi-language support**: Classification in multiple languages
- **Real-time learning**: Continuous improvement from user feedback
- **Advanced caching**: Redis-based distributed caching
- **Model ensemble**: Combine multiple models for better accuracy

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review Ollama documentation: https://ollama.ai/docs
3. Check the test files for usage examples
4. Monitor logs for detailed error information 