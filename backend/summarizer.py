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
    model: str = "llama-3.3-70b-versatile",
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
        f"Format your response using Markdown:\n"
        f"Focus ONLY on clear, well-structured text with appropriate headings. "
        f"If relevant, include main debates, viewpoints, context, definitions, and a high-level synthesis. "
        f"CONTENT:\n{content}\n\n"
        f"===\n\n"
        f"ANSWER (in Markdown format):\n"
        f""
    )

    client = Groq(api_key=api_key)
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a world-class expert writer and summarizer. Format your responses using ONLY simple Markdown with clear headings and plain text. Use ONLY headings (#, ##, ###) and plain text paragraphs. DO NOT use tables, code blocks, bullet points, numbered lists, bold, italic, or any other Markdown formatting that might cause rendering issues. Focus on clear, readable content with a logical heading structure."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=max_tokens,
        temperature=temperature
    )

    summary = completion.choices[0].message.content.strip()
    return summary