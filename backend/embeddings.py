from sentence_transformers import SentenceTransformer
import numpy as np

# Use the same model as the classifier for consistency
model = SentenceTransformer('all-MiniLM-L6-v2')

def get_embedding(text):
    """Generate embedding vector for text using sentence transformers"""
    try:
        # Generate embedding
        embedding = model.encode(text)
        
        # Convert to numpy array for consistency
        embedding_array = np.array(embedding)
        
        print(f"Generated embedding for: '{text[:50]}...'")
        print(f"  Embedding shape: {embedding_array.shape}")
        print(f"  Embedding norm: {np.linalg.norm(embedding_array):.3f}")
        
        return embedding_array
        
    except Exception as e:
        print(f"✗ Error generating embedding: {e}")
        # Return a zero vector as fallback
        return np.zeros(384)  # all-MiniLM-L6-v2 produces 384-dimensional embeddings

def get_embeddings_batch(texts):
    """Generate embeddings for a batch of texts"""
    try:
        embeddings = model.encode(texts)
        return np.array(embeddings)
    except Exception as e:
        print(f"✗ Error generating batch embeddings: {e}")
        return np.zeros((len(texts), 384))

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
        print(f"✗ Error calculating similarity: {e}")
        return 0.0

def test_embeddings():
    """Test embedding functionality"""
    print("Testing embedding functionality...")
    
    # Test single embedding
    text1 = "What is the capital of France?"
    embedding1 = get_embedding(text1)
    
    text2 = "What is the capital of France?"
    embedding2 = get_embedding(text2)
    
    text3 = "What is the weather like today?"
    embedding3 = get_embedding(text3)
    
    # Test similarities
    sim_same = cosine_similarity(embedding1, embedding2)
    sim_different = cosine_similarity(embedding1, embedding3)
    
    print(f"\nSimilarity between identical queries: {sim_same:.3f}")
    print(f"Similarity between different queries: {sim_different:.3f}")
    
    # Test batch embeddings
    texts = ["Query 1", "Query 2", "Query 3"]
    batch_embeddings = get_embeddings_batch(texts)
    print(f"Batch embeddings shape: {batch_embeddings.shape}")

if __name__ == "__main__":
    test_embeddings() 