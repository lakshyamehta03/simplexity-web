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
                min_length=30,
                max_length=150,  # Shorter summary for faster generation
                no_repeat_ngram_size=2,
                repetition_penalty=1.2,
                num_beams=2,  # Fewer beams for speed
                early_stopping=True,
                truncation=True,
                do_sample=False  # Deterministic for speed
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

    # Combine all texts into one string, but limit total length
    combined_text = "\n".join(texts)
    
    # Limit text length to prevent memory issues
    if len(combined_text) > 4000:
        combined_text = combined_text[:4000] + "..."
    
    if query:
        # Add query context but keep it concise
        prompt = f"Query: {query}\n\nContent: {combined_text}"
    else:
        prompt = combined_text

    summarizer = get_summarizer()
    
    try:
        # Use cross-platform timeout
        result = summarize_with_timeout(summarizer, prompt, timeout_seconds)
        
        if result is None:
            return f"Summary: Based on the available content, here's what was found regarding '{query}' if provided. The content has been processed but summarization took too long."
        
        summary = result[0]["summary_text"].strip()
        
        # Ensure summary is relevant to query
        if query and len(summary) > 0:
            # Add query context to summary
            summary = f"Based on the query '{query}': {summary}"
        
        return summary
        
    except Exception as e:
        print(f"Summarization error: {e}")
        return f"Error generating summary: {str(e)}" 