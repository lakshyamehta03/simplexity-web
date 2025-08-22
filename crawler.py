import asyncio
import aiohttp  # pip install aiohttp
import trafilatura
import markdownify

URLS = [
    "https://www.bbc.com/news/technology-67204844",
    "https://www.nytimes.com/2025/07/10/technology/ai-crawlers-news.html",
    "https://edition.cnn.com/2025/07/10/tech/ai-crawler-ban-explained/index.html",
    "https://www.theverge.com/2025/07/10/ai-web-crawler-ethics",
    "https://www.reuters.com/technology/ai-crawling-disputes-2025-07-10/",
    "https://www.techcrunch.com/2025/07/10/ai-crawler-scaling/"
]

async def fetch_and_extract(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            html = await response.text()
    # Try trafilatura first:
    downloaded = trafilatura.fetch_url(url)
    if downloaded:
        text = trafilatura.extract(downloaded, include_formatting=True)
    else:
        text = markdownify.markdownify(html, heading_style="ATX", strip=['script', 'style'])
    return {'url': url, 'content': text[:500]}  # Truncate for preview

async def main():
    tasks = [fetch_and_extract(url) for url in URLS]
    results = await asyncio.gather(*tasks)
    for result in results:
        print(f"\n# {result['url']}\n\n{result['content']}\n{'='*40}")

if __name__ == "__main__":
    asyncio.run(main())
