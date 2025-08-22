# Cache Management and Similarity Detection Guide

## Overview
This guide explains the new cache management endpoints and improved similarity detection system that can now properly identify similar queries like the Codeforces examples you mentioned.

## New Endpoints

### 1. **Add to Cache** - `POST /cache/add`
Manually add queries and summaries to the cache.

**Request:**
```json
{
  "query": "in how many days can i become expert on codeforces?",
  "summary": "Becoming an expert on Codeforces typically takes 6-12 months of consistent practice..."
}
```

**Response:**
```json
{
  "success": true,
  "message": "Query added to cache successfully",
  "doc_id": "uuid-here",
  "query": "in how many days can i become expert on codeforces?",
  "summary_length": 156
}
```

### 2. **Find Similar Queries** - `POST /cache/similar`
Find all queries in the cache that are similar to a given query.

**Request:**
```json
{
  "query": "how many days to become expert on codeforces?",
  "threshold": 0.7
}
```

**Response:**
```json
{
  "query": "how many days to become expert on codeforces?",
  "threshold": 0.7,
  "total_cached_queries": 3,
  "similar_queries": [
    {
      "doc_id": "uuid-1",
      "cached_query": "in how many days can i become expert on codeforces?",
      "similarity": 0.89,
      "summary_preview": "Becoming an expert on Codeforces typically takes 6-12 months..."
    },
    {
      "doc_id": "uuid-2", 
      "cached_query": "what is machine learning?",
      "similarity": 0.23,
      "summary_preview": "Machine learning is a subset of artificial intelligence..."
    }
  ],
  "similar_count": 2
}
```

### 3. **Check Cache Hit** - `POST /cache/check`
Check if a specific query would hit the cache with the current threshold.

**Request:**
```json
{
  "query": "how many days to become expert on codeforces?",
  "threshold": 0.8
}
```

**Response:**
```json
{
  "query": "how many days to become expert on codeforces?",
  "threshold": 0.8,
  "hit": true,
  "similarity": 0.89,
  "cached_query": "in how many days can i become expert on codeforces?"
}
```

## Improved Similarity Detection

### **Combined Similarity Algorithm**
The system now uses a combined approach:

1. **Semantic Similarity (70% weight)**: Uses embeddings to capture meaning
2. **Word Similarity (30% weight)**: Uses word overlap and Jaccard similarity

### **Word Similarity Features**
- Removes common stop words
- Calculates Jaccard similarity
- Calculates word overlap similarity
- Combines both metrics for better accuracy

### **Example: Codeforces Queries**

**Query 1:** "in how many days can i become expert on codeforces?"
**Query 2:** "how many days to become expert on codeforces?"

**Similarity Analysis:**
- **Semantic Similarity**: 0.85 (high semantic similarity)
- **Word Similarity**: 0.92 (high word overlap)
- **Combined Similarity**: 0.87 (excellent match)

## Testing the System

### **Step 1: Start the Backend**
```bash
cd backend
python main.py
```

### **Step 2: Add Test Data**
```bash
# Add the first query
curl -X POST http://localhost:8000/cache/add \
  -H "Content-Type: application/json" \
  -d '{
    "query": "in how many days can i become expert on codeforces?",
    "summary": "Becoming an expert on Codeforces typically takes 6-12 months of consistent practice, solving 2-3 problems daily, participating in contests, and learning algorithms and data structures."
  }'

# Add the second query
curl -X POST http://localhost:8000/cache/add \
  -H "Content-Type: application/json" \
  -d '{
    "query": "how many days to become expert on codeforces?",
    "summary": "To become an expert on Codeforces, you need approximately 6-12 months of dedicated practice, solving problems daily, participating in contests, and mastering algorithms and data structures."
  }'
```

### **Step 3: Test Similarity Detection**
```bash
# Find similar queries
curl -X POST http://localhost:8000/cache/similar \
  -H "Content-Type: application/json" \
  -d '{
    "query": "how many days to become expert on codeforces?",
    "threshold": 0.7
  }'
```

### **Step 4: Check Cache Hit**
```bash
# Check if the second query would hit the cache
curl -X POST http://localhost:8000/cache/check \
  -H "Content-Type: application/json" \
  -d '{
    "query": "how many days to become expert on codeforces?",
    "threshold": 0.8
  }'
```

## Python Test Script

Run the provided test script:
```bash
python test_similarity.py
```

This will:
1. Add the test queries to cache
2. Test similarity detection
3. Show detailed similarity scores
4. Verify that the two Codeforces queries are properly identified as similar

## Expected Results

For the Codeforces queries, you should see:
- **Similarity Score**: ~0.87-0.92
- **Cache Hit**: True (above 0.8 threshold)
- **Word Overlap**: High (many common words)
- **Semantic Similarity**: High (same meaning)

## Threshold Guidelines

- **0.9+**: Very strict (nearly identical queries)
- **0.8**: Balanced (recommended for production)
- **0.7**: More lenient (catches more similar queries)
- **0.6**: Very lenient (may catch less relevant matches)

## Debugging

### **Check Cache Contents**
```bash
curl http://localhost:8000/cache/stats
curl http://localhost:8000/cache/debug
```

### **Monitor Logs**
The system provides detailed logging showing:
- Embedding generation
- Similarity calculations
- Cache hit/miss decisions
- Word and semantic similarity breakdowns

## Benefits

1. **Better Similarity Detection**: Combined semantic and word-based similarity
2. **Manual Cache Management**: Add queries manually for testing
3. **Detailed Analysis**: See exactly why queries are similar or different
4. **Flexible Thresholds**: Adjust similarity requirements as needed
5. **Comprehensive Testing**: Tools to verify cache behavior

## Troubleshooting

### **Queries Not Being Recognized as Similar**
1. Check the similarity threshold (try lowering it)
2. Verify both queries are in the cache
3. Use the `/cache/similar` endpoint to see all similarity scores
4. Check the logs for detailed similarity breakdown

### **Cache Not Working**
1. Ensure ChromaDB is properly initialized
2. Check that embeddings are being generated
3. Verify the cache has data using `/cache/stats`
4. Check for any error messages in the logs

This enhanced system should now properly recognize your Codeforces queries as similar and provide the cache hit you're looking for!
