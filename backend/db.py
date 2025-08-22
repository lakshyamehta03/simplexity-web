import chromadb
from chromadb.config import Settings
import os
from embeddings import get_embedding
import numpy as np
import uuid
from typing import Dict, List, Optional, Any

# Initialize ChromaDB
client = chromadb.PersistentClient(path="./chroma_db", settings=Settings(anonymized_telemetry=False))

# Create or get collection
try:
    collection = client.get_collection("query_cache")
except:
    collection = client.create_collection("query_cache")

def add_to_db(embedding, content, metadata=None):
    """Add query and summary to ChromaDB with vector embedding"""
    try:
        # Generate unique ID for this entry
        doc_id = str(uuid.uuid4())
        
        # Prepare metadata
        meta = metadata or {}
        meta['timestamp'] = str(np.datetime64('now'))
        
        # Add to collection
        collection.add(
            embeddings=[embedding.tolist()],
            documents=[content],
            metadatas=[meta],
            ids=[doc_id]
        )
        
        print(f"✓ Added to cache: {doc_id}")
        print(f"  Query: {meta.get('query', 'Unknown')}")
        print(f"  Content length: {len(content)} characters")
        
        return doc_id
        
    except Exception as e:
        print(f"✗ Error adding to cache: {e}")
        return None

def query_db(embedding, query_text="", top_k=3, similarity_threshold=0.8):
    """Query ChromaDB for similar queries using vector similarity"""
    try:
        print(f"    🔍 Querying ChromaDB cache...")
        print(f"      Query text: '{query_text}'")
        print(f"      Top-k: {top_k}")
        print(f"      Threshold: {similarity_threshold}")
        
        # Query the collection
        results = collection.query(
            query_embeddings=[embedding.tolist()],
            n_results=top_k,
            include=['documents', 'metadatas', 'distances']
        )
        
        print(f"    📊 Raw ChromaDB results:")
        print(f"      IDs: {results['ids']}")
        print(f"      Distances: {results['distances']}")
        print(f"      Documents count: {len(results['documents'][0]) if results['documents'] else 0}")
        
        if not results['ids'] or not results['ids'][0]:
            print(f"    ❌ No results found in cache")
            return None
        
        # Get the best match
        best_match_idx = 0
        best_distance = results['distances'][0][best_match_idx]
        best_similarity = 1 - best_distance  # Convert distance to similarity
        
        # Get cached query for additional similarity check
        cached_query = results['metadatas'][0][best_match_idx].get('query', '')
        
        # Calculate additional similarity metrics
        word_similarity = calculate_word_similarity(query_text, cached_query)
        semantic_similarity = best_similarity
        
        # Combine similarities (weighted average)
        combined_similarity = (semantic_similarity * 0.7) + (word_similarity * 0.3)
        
        print(f"    🎯 Best match analysis:")
        print(f"      Best distance: {best_distance:.3f}")
        print(f"      Semantic similarity: {semantic_similarity:.3f}")
        print(f"      Word similarity: {word_similarity:.3f}")
        print(f"      Combined similarity: {combined_similarity:.3f}")
        print(f"      Threshold: {similarity_threshold}")
        
        # Check if combined similarity meets threshold
        if combined_similarity >= similarity_threshold:
            print(f"    ✅ Cache hit! Combined similarity: {combined_similarity:.3f} >= threshold: {similarity_threshold}")
            
            # Get the best match
            best_document = results['documents'][0][best_match_idx]
            best_metadata = results['metadatas'][0][best_match_idx]
            
            # Add similarity to metadata
            best_metadata['similarity'] = combined_similarity
            best_metadata['semantic_similarity'] = semantic_similarity
            best_metadata['word_similarity'] = word_similarity
            
            print(f"    📄 Retrieved document length: {len(best_document)} characters")
            print(f"    🏷️  Metadata: {best_metadata}")
            
            return {
                'documents': [best_document],
                'metadatas': [best_metadata],
                'distances': [results['distances'][0][best_match_idx]],
                'ids': [results['ids'][0][best_match_idx]],
                'similarity': combined_similarity
            }
        else:
            print(f"    ❌ Cache miss. Combined similarity {combined_similarity:.3f} < threshold {similarity_threshold}")
            return None
            
    except Exception as e:
        print(f"    💥 Error querying cache: {e}")
        return None

def calculate_word_similarity(query1, query2):
    """Calculate word-based similarity between two queries"""
    try:
        # Normalize queries
        query1_words = set(query1.lower().split())
        query2_words = set(query2.lower().split())
        
        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'}
        
        query1_words = query1_words - stop_words
        query2_words = query2_words - stop_words
        
        if not query1_words and not query2_words:
            return 1.0  # Both queries are empty after removing stop words
        
        if not query1_words or not query2_words:
            return 0.0  # One query is empty
        
        # Calculate Jaccard similarity
        intersection = len(query1_words.intersection(query2_words))
        union = len(query1_words.union(query2_words))
        
        jaccard_similarity = intersection / union if union > 0 else 0.0
        
        # Calculate word overlap similarity
        overlap_similarity = intersection / max(len(query1_words), len(query2_words))
        
        # Combine both metrics
        word_similarity = (jaccard_similarity * 0.6) + (overlap_similarity * 0.4)
        
        return word_similarity
        
    except Exception as e:
        print(f"Error calculating word similarity: {e}")
        return 0.0

def clear_cache():
    """Clear all cached queries"""
    try:
        # Delete the collection and recreate it
        client.delete_collection("query_cache")
        global collection
        collection = client.create_collection("query_cache")
        print("✓ Cache cleared successfully")
    except Exception as e:
        print(f"✗ Error clearing cache: {e}")

def get_cache_stats():
    """Get cache statistics"""
    try:
        count = collection.count()
        print(f"Cache contains {count} entries")
        return count
    except Exception as e:
        print(f"✗ Error getting cache stats: {e}")
        return 0

def list_cached_queries():
    """List all cached queries"""
    try:
        # Get all documents
        results = collection.get()
        
        queries = []
        if results['metadatas']:
            for metadata in results['metadatas']:
                query = metadata.get('query', 'Unknown')
                timestamp = metadata.get('timestamp', 'Unknown')
                queries.append({
                    'query': query,
                    'timestamp': timestamp
                })
        
        print(f"Found {len(queries)} cached queries")
        return queries
        
    except Exception as e:
        print(f"✗ Error listing cached queries: {e}")
        return []

def debug_cache_content():
    """Debug cache contents with detailed information"""
    try:
        print("\n" + "=" * 60)
        print("CACHE DEBUG INFORMATION")
        print("=" * 60)
        
        # Get cache stats
        count = get_cache_stats()
        print(f"Total entries: {count}")
        
        if count == 0:
            print("Cache is empty")
            return
        
        # Get all documents
        results = collection.get()
        
        print(f"\nCached Entries:")
        print("-" * 40)
        
        for i, (doc_id, document, metadata) in enumerate(zip(
            results['ids'], 
            results['documents'], 
            results['metadatas']
        )):
            print(f"\nEntry {i+1}:")
            print(f"  ID: {doc_id}")
            print(f"  Query: {metadata.get('query', 'Unknown')}")
            print(f"  Timestamp: {metadata.get('timestamp', 'Unknown')}")
            print(f"  Content length: {len(document)} characters")
            print(f"  Content preview: {document[:100]}...")
        
        print("\n" + "=" * 60)
        
    except Exception as e:
        print(f"✗ Error debugging cache: {e}")

def test_cache_functionality():
    """Test cache functionality"""
    print("\nTesting cache functionality...")
    
    # Test adding to cache
    test_embedding = get_embedding("test query")
    test_content = "This is a test summary for testing cache functionality."
    test_metadata = {"query": "test query"}
    
    print("\n1. Adding test entry to cache...")
    doc_id = add_to_db(test_embedding, test_content, test_metadata)
    
    if doc_id:
        print("✓ Test entry added successfully")
        
        # Test querying cache
        print("\n2. Querying cache for similar query...")
        query_embedding = get_embedding("test query")
        result = query_db(query_embedding, "test query", top_k=1, similarity_threshold=0.8)
        
        if result:
            print("✓ Cache query successful")
            print(f"  Retrieved content: {result['documents'][0][:50]}...")
        else:
            print("✗ Cache query failed")
        
        # Test cache stats
        print("\n3. Getting cache stats...")
        count = get_cache_stats()
        print(f"  Cache count: {count}")
        
        # Test listing queries
        print("\n4. Listing cached queries...")
        queries = list_cached_queries()
        print(f"  Found {len(queries)} queries")
        
    else:
        print("✗ Failed to add test entry")

if __name__ == "__main__":
    test_cache_functionality() 