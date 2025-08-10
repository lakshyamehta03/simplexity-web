from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import requests
import time
import re
import json
import os
import concurrent.futures
from urllib.parse import urlparse
from typing import List, Dict, Any

def setup_driver():
    """Setup Chrome driver with optimal settings for better anti-bot evasion"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-plugins")
    chrome_options.add_argument("--disable-images")  # Faster loading
    chrome_options.add_argument("--disable-javascript")  # Sometimes helps with anti-bot
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_experimental_option("prefs", {
        "profile.default_content_setting_values.notifications": 2,
        "profile.default_content_settings.popups": 0
    })
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
    driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']})")
    return driver

def scrape_content(url, timeout=15):
    """Scrape content from a URL using Selenium and BeautifulSoup with better error handling"""
    driver = None
    content = ""
    
    try:
        print(f"Scraping: {url}")
        
        # Try with JavaScript disabled first (faster, less likely to be blocked)
        content = try_scrape_with_js_disabled(url, timeout)
        
        # If that fails, try with JavaScript enabled
        if not content or len(content.strip()) < 50:
            print("JavaScript-disabled scraping failed, trying with JavaScript enabled...")
            content = try_scrape_with_js_enabled(url, timeout)
        
        if content:
            print(f"Successfully extracted {len(content)} characters")
        else:
            print("All scraping methods failed")
        
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        content = ""
    
    return content

def try_scrape_with_js_disabled(url, timeout):
    """Try scraping with JavaScript disabled"""
    driver = None
    try:
        driver = setup_driver()
        driver.set_page_load_timeout(timeout)
        driver.get(url)
        
        # Wait for page to load
        wait = WebDriverWait(driver, timeout)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
            script.decompose()
        
        content = extract_content_advanced(soup, url)
        
        if not content or len(content.strip()) < 50:
            content = extract_content_fallback(soup)
        
        content = clean_content(content)
        
        return content if len(content.strip()) >= 50 else ""
        
    except Exception as e:
        print(f"JavaScript-disabled scraping failed: {e}")
        return ""
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

def try_scrape_with_js_enabled(url, timeout):
    """Try scraping with JavaScript enabled"""
    driver = None
    try:
        # Create driver with JavaScript enabled
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        driver.set_page_load_timeout(timeout)
        driver.get(url)
        
        # Wait longer for JavaScript to load
        wait = WebDriverWait(driver, timeout)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(2)  # Wait for dynamic content
        
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
            script.decompose()
        
        content = extract_content_advanced(soup, url)
        
        if not content or len(content.strip()) < 50:
            content = extract_content_fallback(soup)
        
        content = clean_content(content)
        
        return content if len(content.strip()) >= 50 else ""
        
    except Exception as e:
        print(f"JavaScript-enabled scraping failed: {e}")
        return ""
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

def extract_content_advanced(soup, url):
    """Advanced content extraction using multiple strategies with query relevance"""
    content_parts = []
    
    # Strategy 1: Look for main content areas (highest priority)
    main_selectors = [
        'main',
        '[role="main"]',
        '.main-content',
        '.content',
        '.article-content',
        '.post-content',
        '.entry-content',
        '#content',
        '#main',
        '.main'
    ]
    
    for selector in main_selectors:
        elements = soup.select(selector)
        for element in elements:
            text = element.get_text(separator=' ', strip=True)
            if len(text) > 300:  # Increased minimum length
                content_parts.append(text)
    
    # Strategy 2: Look for article content
    article_selectors = [
        'article',
        '.article',
        '.post',
        '.entry',
        '.story',
        '.blog-post'
    ]
    
    for selector in article_selectors:
        elements = soup.select(selector)
        for element in elements:
            text = element.get_text(separator=' ', strip=True)
            if len(text) > 300:
                content_parts.append(text)
    
    # Strategy 3: Look for paragraphs with substantial content
    paragraphs = soup.find_all('p')
    paragraph_text = []
    for p in paragraphs:
        text = p.get_text(strip=True)
        # Filter out navigation, ads, and short content
        if (len(text) > 80 and 
            not any(skip in text.lower() for skip in ['cookie', 'privacy', 'terms', 'advertisement', 'subscribe', 'newsletter'])):
            paragraph_text.append(text)
    
    if paragraph_text:
        paragraph_text.sort(key=len, reverse=True)
        content_parts.append(' '.join(paragraph_text[:10]))  # Top 10 paragraphs
    
    # Strategy 4: Look for divs with substantial text (but be more selective)
    divs = soup.find_all('div')
    for div in divs:
        # Skip if div has too many child elements (likely navigation/menu)
        if len(div.find_all()) > 15:
            continue
        
        text = div.get_text(separator=' ', strip=True)
        # More strict filtering
        if (len(text) > 200 and 
            not any(skip in text.lower() for skip in ['menu', 'navigation', 'sidebar', 'footer', 'header', 'cookie', 'privacy', 'advertisement'])):
            content_parts.append(text)
    
    # Strategy 5: Look for specific content containers
    content_selectors = [
        '.text-content',
        '.body-content',
        '.page-content',
        '.story-content',
        '.post-body',
        '.entry-body'
    ]
    
    for selector in content_selectors:
        elements = soup.select(selector)
        for element in elements:
            text = element.get_text(separator=' ', strip=True)
            if len(text) > 200:
                content_parts.append(text)
    
    # Combine all content parts and filter
    if content_parts:
        combined = ' '.join(content_parts)
        # Remove duplicate content
        combined = remove_duplicates(combined)
        return combined
    
    return ""

def remove_duplicates(text):
    """Remove duplicate sentences and phrases"""
    sentences = text.split('. ')
    unique_sentences = []
    seen = set()
    
    for sentence in sentences:
        sentence = sentence.strip()
        if sentence and len(sentence) > 20:
            # Create a simple hash of the sentence
            sentence_hash = sentence.lower().replace(' ', '')[:50]
            if sentence_hash not in seen:
                seen.add(sentence_hash)
                unique_sentences.append(sentence)
    
    return '. '.join(unique_sentences)

def extract_content_fallback(soup):
    """Fallback content extraction"""
    # Get all text from body
    body = soup.find('body')
    if body:
        return body.get_text(separator=' ', strip=True)
    
    return soup.get_text(separator=' ', strip=True)

def clean_content(content):
    """Clean and format the extracted content"""
    if not content:
        return ""
    
    # Remove extra whitespace
    content = re.sub(r'\s+', ' ', content)
    
    # Remove common unwanted patterns
    unwanted_patterns = [
        r'cookie|privacy policy|terms of service|advertisement|advertise|ads',
        r'subscribe|newsletter|sign up|log in|login|register|signup|signin',
        r'facebook|twitter|instagram|linkedin|youtube|social media',
        r'©|copyright|all rights reserved|powered by',
        r'loading\.\.\.|please wait\.\.\.|loading|please wait',
        r'javascript:|function\(|var\s+\w+|console\.log',
        r'\[.*?\]',  # Remove text in brackets
        r'\{.*?\}',  # Remove text in braces
        r'click here|read more|learn more|find out more',
        r'home|about|contact|support|help',
        r'search|menu|navigation|sidebar|footer|header',
        r'email|phone|address|location',
        r'follow us|share this|like us',
        r'free trial|download|install|get started',
        r'newsletter|email updates|stay updated',
    ]
    
    for pattern in unwanted_patterns:
        content = re.sub(pattern, '', content, flags=re.IGNORECASE)
    
    # Remove very short lines and filter by quality
    lines = content.split('. ')
    cleaned_lines = []
    for line in lines:
        line = line.strip()
        # More strict filtering - keep only substantial, meaningful content
        if (len(line) > 30 and 
            not any(skip in line.lower() for skip in ['cookie', 'privacy', 'terms', 'advertisement', 'subscribe', 'newsletter', 'click here', 'read more'])):
            cleaned_lines.append(line)
    
    content = '. '.join(cleaned_lines)
    
    # Final cleanup
    content = re.sub(r'\s+', ' ', content)
    content = content.strip()
    
    return content
    content = content.strip()
    
    return content

def scrape_multiple_urls(urls, save_to_files=True, output_dir="scraped_content", max_workers=5):
    """Scrape content from multiple URLs in parallel"""
    results = []
    successful_scrapes = 0
    start_time = time.time()
    
    # Create output directory if saving to files
    if save_to_files:
        os.makedirs(output_dir, exist_ok=True)
    
    print(f"Starting parallel scraping of {len(urls)} URLs with {max_workers} workers...")
    
    # Define a worker function to process each URL
    def process_url(url_data):
        idx, url = url_data
        try:
            print(f"Scraping URL {idx}/{len(urls)}: {url}")
            content = scrape_content(url)
            success = len(content) > 100
            
            result = {
                'url': url,
                'content': content,
                'length': len(content),
                'success': success
            }
            
            # Save to file if requested
            if save_to_files and content:
                domain = urlparse(url).netloc.replace('.', '_')
                filename = f"{output_dir}/content_{idx}_{domain}.txt"
                
                try:
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(f"URL: {url}\n")
                        f.write(f"Length: {len(content)} characters\n")
                        f.write("-" * 50 + "\n")
                        f.write(content)
                    print(f"✓ Saved to: {filename}")
                except Exception as e:
                    print(f"✗ Error saving file: {e}")
            
            if success:
                print(f"✓ Successfully scraped {len(content)} characters from {url}")
            else:
                print(f"✗ Insufficient content from {url}")
                
            return result
        except Exception as e:
            print(f"✗ Error scraping {url}: {str(e)}")
            return {
                'url': url,
                'content': "",
                'length': 0,
                'success': False,
                'error': str(e)
            }
    
    # Use ThreadPoolExecutor for parallel processing
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all scraping tasks
        future_to_url = {executor.submit(process_url, (i, url)): url 
                         for i, url in enumerate(urls, 1)}
        
        # Process results as they complete
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                result = future.result()
                results.append(result)
                if result['success']:
                    successful_scrapes += 1
            except Exception as e:
                print(f"✗ Error processing result for {url}: {str(e)}")
                results.append({
                    'url': url,
                    'content': "",
                    'length': 0,
                    'success': False,
                    'error': str(e)
                })
    
    # Save summary JSON
    if save_to_files:
        summary_file = f"{output_dir}/scraping_summary.json"
        try:
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"\nSummary saved to: {summary_file}")
        except Exception as e:
            print(f"Error saving summary: {e}")
    
    elapsed_time = time.time() - start_time
    print(f"\nParallel scraping completed in {elapsed_time:.2f} seconds")
    print(f"Success: {successful_scrapes}/{len(urls)} URLs")
    
    return results

if __name__ == "__main__":
    # Test the scraper
    print("Content Scraper Test")
    print("=" * 50)
    
    # Get URLs from user
    urls_input = input("Enter URLs (comma-separated): ")
    urls = [url.strip() for url in urls_input.split(',') if url.strip()]
    
    if not urls:
        print("No URLs provided. Using test URL...")
        urls = ["https://example.com"]
    
    # Scrape content
    results = scrape_multiple_urls(urls)
    
    # Display results
    print(f"\nScraping Results:")
    print("=" * 50)
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result['url']}")
        print(f"   Success: {result['success']}")
        print(f"   Length: {result['length']} characters")
        if result['content']:
            print(f"   Preview: {result['content'][:200]}...")