from sentence_transformers import SentenceTransformer
import numpy as np

# Use the same model as the classifier for consistency

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

if __name__ == "__main__":
    test_embeddings() 