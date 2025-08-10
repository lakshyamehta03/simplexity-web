import trafilatura
import requests
import markdownify
import os

def extract_and_format(url):
    """
    Download webpage, extract main content, format as Markdown.
    Works for most news, blog, and article pages.
    """
    # Fetch raw HTML
    response = requests.get(
        url,
        headers={'User-Agent': 'Mozilla/5.0'}
    )
    html_content = response.text

    # Try Trafilatura for clean, structured extraction
    downloaded = trafilatura.fetch_url(url)
    text = None
    if downloaded:
        text = trafilatura.extract(downloaded, include_formatting=True)
    
    # Fallback: HTML → Markdown conversion if Trafilatura fails
    if text is None or len(text.strip()) < 100:
        text = markdownify.markdownify(
            html_content,
            heading_style="ATX",
            strip=['script', 'style']
        )

    # Extract page title (optional)
    title = None
    if '<title>' in html_content:
        start = html_content.find('<title>') + 7
        end = html_content.find('</title>')
        title = html_content[start:end].strip()

    return {
        'title': title,
        'content_markdown': text
    }

def save_to_file(content, filename="output.md"):
    """Save extracted markdown content into a file."""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[✅] Content saved to {os.path.abspath(filename)}")

# Example usage
if __name__ == "__main__":
    url = "https://www.espncricinfo.com/team/india-6/match-schedule-fixtures-and-results"
    result = extract_and_format(url)
    markdown_output = f"# {result['title']}\n\n{result['content_markdown']}"
    save_to_file(markdown_output, "article_output.md")