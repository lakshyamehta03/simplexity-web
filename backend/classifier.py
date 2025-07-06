from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd

# Load the sentence transformer model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Load examples from queries.csv
def load_examples_from_csv():
    """Load valid and invalid examples from queries.csv"""
    try:
        df = pd.read_csv("queries.csv")
        
        # Clean the data: remove NaN values and empty strings
        df = df.dropna()
        df = df[df['text'].str.strip() != '']
        
        valid_examples = df[df['label'] == 'valid']['text'].tolist()
        invalid_examples = df[df['label'] == 'invalid']['text'].tolist()
        
        # Additional filtering to ensure all examples are valid strings
        valid_examples = [str(ex).strip() for ex in valid_examples if str(ex).strip()]
        invalid_examples = [str(ex).strip() for ex in invalid_examples if str(ex).strip()]
        
        print(f"Loaded {len(valid_examples)} valid examples and {len(invalid_examples)} invalid examples")
        return valid_examples, invalid_examples
    except Exception as e:
        print(f"Error loading examples from CSV: {e}")
        # Fallback to default examples
        return [
            "What is the weather today?",
            "How to cook pasta?",
            "Best restaurants in New York"
        ], [
            "Set alarm for 6am",
            "Remind me to buy milk",
            "Call mom at 6pm"
        ]

# Load examples from CSV
VALID_EXAMPLES, INVALID_EXAMPLES = load_examples_from_csv()

# Pre-compute embeddings for examples
VALID_EMBEDDINGS = model.encode(VALID_EXAMPLES)
INVALID_EMBEDDINGS = model.encode(INVALID_EXAMPLES)

def is_valid_query(query):
    """Classify if a query is valid using similarity to examples from queries.csv"""
    if not query or not query.strip():
        return False
    
    # Encode the query
    query_embedding = model.encode([query])
    
    # Calculate similarity with valid examples
    valid_similarities = cosine_similarity(query_embedding, VALID_EMBEDDINGS)[0]
    max_valid_similarity = np.max(valid_similarities)
    
    # Calculate similarity with invalid examples
    invalid_similarities = cosine_similarity(query_embedding, INVALID_EMBEDDINGS)[0]
    max_invalid_similarity = np.max(invalid_similarities)
    
    # Use threshold to determine if query is more similar to valid or invalid examples
    threshold = 0.25
    
    if max_valid_similarity > threshold and max_valid_similarity > max_invalid_similarity:
        print(f"Query '{query}' classified as VALID (valid_sim: {max_valid_similarity:.3f}, invalid_sim: {max_invalid_similarity:.3f})")
        return True
    else:
        print(f"Query '{query}' classified as INVALID (valid_sim: {max_valid_similarity:.3f}, invalid_sim: {max_invalid_similarity:.3f})")
        return False