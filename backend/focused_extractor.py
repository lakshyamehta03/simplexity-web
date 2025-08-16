from typing import List, Dict, Optional
import os
from groq import Groq

# Load Groq API key from environment variable
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

def extract_focused_content(query: str, texts: List[str], method: str = "textrank", 
                          sentences_ratio: float = 0.5, groq_model: str = "llama-3.1-8b-instant") -> List[str]:
    """
    Extracts the most relevant passages from scraped content for the given query.
    
    Args:
        query: The user's query
        texts: List of scraped content from different sources
        method: "textrank" or "groq" for extraction method
        sentences_ratio: Ratio of sentences to keep for textrank (0.1-0.5)
        groq_model: Groq model to use for LLM-based extraction
    
    Returns:
        List of focused/filtered content strings
    """
    if not texts:
        return []
    
    focused_texts = []
    
    for i, content in enumerate(texts):
        if not content or len(content.strip()) < 100:  # Skip very short content
            continue
            
        try:
            if method.lower() == "textrank":
                focused_content = extract_with_textrank(content, sentences_ratio)
            elif method.lower() == "groq":
                focused_content = extract_with_groq(query, content, groq_model)
            else:
                # Fallback to simple keyword-based extraction
                focused_content = extract_with_keywords(query, content)
            
            if focused_content and len(focused_content.strip()) > 50:
                focused_texts.append(focused_content)
                print(f"✓ Extracted focused content from source {i+1} ({len(focused_content)} chars)")
            else:
                # If extraction fails, keep original but truncated
                truncated = content[:2000] + "..." if len(content) > 2000 else content
                focused_texts.append(truncated)
                print(f"⚠ Extraction failed for source {i+1}, using truncated original")
                
        except Exception as e:
            print(f"✗ Error extracting from source {i+1}: {e}")
            # Fallback to truncated original content
            truncated = content[:2000] + "..." if len(content) > 2000 else content
            focused_texts.append(truncated)
    
    return focused_texts

def extract_with_textrank(content: str, ratio: float = 0.6) -> str:
    """
    Extract key sentences using TextRank algorithm.
    Falls back to simple sentence selection if summa is not available.
    """
    try:
        from summa import summarize
        # Use higher ratio to preserve more content
        summary = summarize(content, ratio=ratio)
        # If summary is too short, try with higher ratio
        if summary and len(summary) < len(content) * 0.4:
            summary = summarize(content, ratio=min(0.8, ratio + 0.2))
        return summary if summary else content[:4000]
    except ImportError:
        print("⚠ summa library not available, using fallback extraction")
        return extract_with_keywords_fallback(content)
    except Exception as e:
        print(f"⚠ TextRank extraction failed: {e}, using fallback")
        return extract_with_keywords_fallback(content)

def extract_with_groq(query: str, content: str, model: str = "llama-3.1-8b-instant") -> str:
    """
    Extract relevant passages using Groq LLM.
    """
    if not client:
        print("⚠ GROQ_API_KEY not set, falling back to keyword extraction")
        return extract_with_keywords(query, content)
    
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert assistant that extracts only the most relevant passages directly answering the given query from the provided content. Return only the key passages that directly answer the question, maintaining original wording but removing irrelevant sections. Extract comprehensive passages that answer the query while maintaining sufficient context. Include supporting details, examples, and explanations. Aim for thorough coverage rather than brevity."
                },
                {
                    "role": "user",
                    "content": f"QUESTION:\n{query}\n\nDOCUMENT:\n{content[:4000]}\n\nReturn only key passages that directly answer the question. Keep the original wording but remove irrelevant content."
                }
            ],
            temperature=0,
            max_tokens=2048
        )
        
        passages = completion.choices[0].message.content
        return passages if passages else content[:2000]
        
    except Exception as e:
        print(f"⚠ Groq extraction failed: {e}, falling back to keyword extraction")
        return extract_with_keywords(query, content)

def extract_with_keywords(query: str, content: str) -> str:
    """
    Simple keyword-based extraction as fallback method.
    """
    # Split content into sentences
    sentences = content.replace('\n', ' ').split('. ')
    
    # Extract keywords from query (simple approach)
    query_words = set(query.lower().split())
    # Remove common stop words
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'what', 'how', 'why', 'when', 'where'}
    query_words = query_words - stop_words
    
    # Score sentences based on keyword matches
    scored_sentences = []
    for sentence in sentences:
        if len(sentence.strip()) < 20:  # Skip very short sentences
            continue
        
        sentence_lower = sentence.lower()
        score = sum(1 for word in query_words if word in sentence_lower)
        
        if score > 0:
            scored_sentences.append((score, sentence.strip()))
    
    # Sort by score and take top sentences
    scored_sentences.sort(key=lambda x: x[0], reverse=True)
    top_sentences = [sent[1] for sent in scored_sentences[:10]]  # Top 10 sentences
    
    result = '. '.join(top_sentences)
    return result if result else content[:2000]

def extract_with_keywords_fallback(content: str) -> str:
    """
    Simple fallback that takes first and last parts of content.
    """
    if len(content) <= 2000:
        return content
    
    # Take first 1000 and last 1000 characters
    first_part = content[:1000]
    last_part = content[-1000:]
    
    return first_part + "\n\n[...content truncated...]\n\n" + last_part

def save_focused_content(query: str, original_texts: List[str], focused_texts: List[str], output_dir: str = "scraped_content"):
    """
    Save both original and focused content for comparison.
    """
    try:
        os.makedirs(output_dir, exist_ok=True)
        
        # Save focused content for summarizer
        focused_file = os.path.join(output_dir, "focused_content_for_summarizer.txt")
        with open(focused_file, 'w', encoding='utf-8') as f:
            f.write(f"Query: {query}\n")
            f.write(f"Number of focused sources: {len(focused_texts)}\n")
            f.write("=" * 80 + "\n\n")
            for i, text in enumerate(focused_texts, 1):
                f.write(f"FOCUSED SOURCE {i}:\n")
                f.write("-" * 40 + "\n")
                f.write(text)
                f.write("\n\n" + "=" * 80 + "\n\n")
        
        print(f"✓ Focused content saved to: {focused_file}")
        
        # Save comparison file
        comparison_file = os.path.join(output_dir, "content_comparison.txt")
        with open(comparison_file, 'w', encoding='utf-8') as f:
            f.write(f"CONTENT EXTRACTION COMPARISON\n")
            f.write(f"Query: {query}\n")
            f.write("=" * 80 + "\n\n")
            
            for i, (original, focused) in enumerate(zip(original_texts, focused_texts), 1):
                f.write(f"SOURCE {i} COMPARISON:\n")
                f.write("-" * 40 + "\n")
                f.write(f"Original length: {len(original)} characters\n")
                f.write(f"Focused length: {len(focused)} characters\n")
                f.write(f"Reduction: {((len(original) - len(focused)) / len(original) * 100):.1f}%\n\n")
                
                f.write("ORIGINAL:\n")
                f.write(original[:500] + "..." if len(original) > 500 else original)
                f.write("\n\nFOCUSED:\n")
                f.write(focused)
                f.write("\n\n" + "=" * 80 + "\n\n")
        
        print(f"✓ Content comparison saved to: {comparison_file}")
        
    except Exception as e:
        print(f"✗ Error saving focused content: {e}")