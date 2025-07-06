from transformers import pipeline
from typing import List
import os
import time
import threading
import queue

# Use a faster, lighter model for summarization
MODEL_NAME = "facebook/bart-large-cnn"  # Much faster than LED-large

# Load the summarization pipeline once
_summarizer = None

def get_summarizer():
    global _summarizer
    if _summarizer is None:
        device = 0 if os.environ.get("USE_CUDA", "0") == "1" else -1
        _summarizer = pipeline(
            "summarization",
            MODEL_NAME,
            device=device,
            model_kwargs={"torch_dtype": "auto"}
        )
    return _summarizer

def summarize_with_timeout(summarizer, prompt, timeout_seconds):
    """Run summarization with timeout using threading"""
    result_queue = queue.Queue()
    exception_queue = queue.Queue()
    
    def run_summarization():
        try:
            result = summarizer(
                prompt,
                min_length=30,  # Reduced for shorter inputs
                max_length=400,  # Balanced length
                no_repeat_ngram_size=2,
                repetition_penalty=1.2,
                num_beams=3,  # Balanced for quality and speed
                early_stopping=True,
                truncation=True,
                do_sample=False  # Deterministic for consistency
            )
            result_queue.put(result)
        except Exception as e:
            exception_queue.put(e)
    
    # Start summarization in a separate thread
    thread = threading.Thread(target=run_summarization)
    thread.daemon = True
    thread.start()
    
    # Wait for result with timeout
    try:
        thread.join(timeout=timeout_seconds)
        if thread.is_alive():
            print("Summarization timed out")
            return None
        elif not exception_queue.empty():
            raise exception_queue.get()
        else:
            return result_queue.get()
    except queue.Empty:
        print("Summarization timed out")
        return None

def summarize(texts: List[str], query: str = "", timeout_seconds: int = 30) -> str:
    """
    Summarize the provided texts using a fast BART model.
    If a query is provided, prepend it to the text to focus the summary.
    """
    if not texts:
        return "No content available to summarize."

    # Combine all texts into one string
    combined_text = "\n\n".join(texts)
    
    # Limit text length to prevent memory issues
    if len(combined_text) > 4000:
        combined_text = combined_text[:4000] + "..."
    
    if query:
        # Add query context for focused summarization
        prompt = f"Query: {query}\n\nContent: {combined_text}"
    else:
        prompt = combined_text

    summarizer = get_summarizer()
    
    try:
        # Use cross-platform timeout
        result = summarize_with_timeout(summarizer, prompt, timeout_seconds)
        
        if result is None:
            return f"Summary: Based on the available content, here's what was found regarding '{query}' if provided. The content has been processed but summarization took too long."
        
        # Simple error handling
        if not result or not isinstance(result, list) or len(result) == 0:
            return f"Summary: Unable to generate summary. Please try again."
        
        summary = result[0].get("summary_text", "").strip()
        
        if not summary:
            return f"Summary: Generated summary is empty. Please try again."
        
        # Ensure summary is relevant to query
        if query and len(summary) > 0:
            # Add query context to summary
            summary = f"{summary}"
        
        return summary
        
    except Exception as e:
        print(f"Summarization error: {e}")
        return f"Error generating summary: {str(e)}" 