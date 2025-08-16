from groq import Groq
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env
load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")


def summarize(
    focused_content: list[str],
    query: str = "",
    api_key: str = None,
    model: str = "llama3-70b-8192",
    max_tokens: int = 4096,
    temperature: float = 0.3
):
    """
    Summarizes the contents of a list of strings using Groq LLM, tailored to a query.
    """
    if api_key is None:
        api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise ValueError("You must provide a GROQ_API_KEY!")

    if not focused_content or not isinstance(focused_content, list):
        return "Provided content must be a non-empty list of strings."

    # Join the list of strings into one coherent content block
    content = "\n".join(focused_content)

    # Build the prompt
    prompt = (
        f"Question: {query}\n\n"
        f"Carefully read the following focused content extracted from multiple sources. "
        f"Write a comprehensive, long, detailed, and well-structured answer to the user's question. "
        f"If relevant, include main debates, viewpoints, context, definitions, and a high-level synthesis. "
        f"Focus only on facts and reasoning found in the provided content. "
        f"Do not provide generic or out-of-scope information.\n\n"
        f"CONTENT:\n{content}\n\n"
        f"===\n\n"
        f"ANSWER:"
    )

    client = Groq(api_key=api_key)
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a world-class expert writer and summarizer."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=max_tokens,
        temperature=temperature
    )

    summary = completion.choices[0].message.content.strip()
    return summary

# ------------------------------
# TESTING / USAGE CODE
# ------------------------------
# if __name__ == "__main__":
#     FILEPATH = "scraped_content/focused_content_for_summarizer.txt"
#     QUERY = "What is the capital of india? how did it become so?"  # Change as needed

#     # Set your Groq API key
#     GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")  # Or set as a string directly

#     print(f"Summarizing '{FILEPATH}' via Groq for query: {QUERY}\n")
#     summary = summarize(
#         file_path=FILEPATH,
#         query=QUERY,
#         api_key=GROQ_API_KEY,
#         model="llama3-70b-8192",   # Or "mixtral-8x7b-32768" for very long docs/answers
#         max_tokens=4096,           # Increase as needed; Groq supports >4k output
#         temperature=0.3
#     )
#     print("Current working directory:", os.getcwd())
#     print("\n================ SUMMARY ================\n")
#     print(summary)
#     print("\n=========================================")