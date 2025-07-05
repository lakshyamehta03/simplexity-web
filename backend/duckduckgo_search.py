from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
import time

def setup_driver():
    """Setup Chrome driver with optimal settings"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def search_duckduckgo(query, num_results=5):
    """Search DuckDuckGo and return list of URLs"""
    results = []
    driver = None
    
    try:
        print(f"Searching DuckDuckGo for: '{query}'")
        print(f"Requesting {num_results} results...")
        
        # Initialize driver
        driver = setup_driver()
        
        # Navigate to DuckDuckGo
        search_url = f"https://duckduckgo.com/?va=j&t=hc&q={query}"
        print(f"Navigating to: {search_url}")
        driver.get(search_url)
        
        # Wait for page to load completely
        wait = WebDriverWait(driver, 15)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        # Additional wait for dynamic content
        print("Waiting for page to load...")
        time.sleep(5)
        
        # Get page source
        page_source = driver.page_source
        print(f"Page source length: {len(page_source)}")
        
        # Check if no results found
        if 'Make sure all words are spelled correctly.' in page_source:
            print("No results found on DuckDuckGo")
            return results
        
        # Try multiple selectors to find search results
        selectors_to_try = [
            "a[data-testid='result-title-a']",
            "a[data-testid='result-title']",
            ".result__title a",
            ".result a",
            "h2 a",
            ".web-result__title a",
            "a[href^='http']"
        ]
        
        all_found_urls = []
        
        for selector in selectors_to_try:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                print(f"Selector '{selector}': Found {len(elements)} elements")
                
                for element in elements:
                    try:
                        url = element.get_attribute('href')
                        if url and url.startswith('http'):
                            all_found_urls.append(url)
                    except:
                        continue
                        
            except Exception as e:
                print(f"Selector '{selector}' failed: {e}")
                continue
        
        # Remove duplicates while preserving order
        unique_urls = []
        seen = set()
        for url in all_found_urls:
            if url not in seen:
                unique_urls.append(url)
                seen.add(url)
        
        print(f"Found {len(unique_urls)} unique URLs from all selectors")
        
        # Filter valid URLs
        valid_urls = []
        for url in unique_urls:
            if is_valid_search_url(url):
                valid_urls.append(url)
                print(f"✓ Valid URL: {url}")
            else:
                print(f"✗ Filtered out: {url}")
        
        print(f"After filtering: {len(valid_urls)} valid URLs")
        
        # Take the requested number of results
        results = valid_urls[:num_results]
        
        # If we still don't have enough results, try regex fallback
        if len(results) < num_results:
            print(f"Only found {len(results)} results, trying regex fallback...")
            regex_results = extract_urls_with_regex(page_source, num_results - len(results))
            results.extend(regex_results)
        
    except Exception as e:
        print(f"DuckDuckGo search error: {e}")
    
    finally:
        if driver:
            try:
                driver.quit()
                print("Browser closed successfully")
            except:
                pass
    
    print(f"Final result: {len(results)} URLs found")
    return results[:num_results]

def extract_urls_with_regex(page_source, max_results):
    """Extract URLs using regex patterns as fallback"""
    url_patterns = [
        r'href="(https?://[^"]*)"',
        r'data-testid="result-title-a"[^>]*href="(https?://[^"]*)"',
        r'<a[^>]*class="[^"]*result[^"]*"[^>]*href="(https?://[^"]*)"',
        r'<a[^>]*data-testid="[^"]*"[^>]*href="(https?://[^"]*)"'
    ]
    
    all_urls = []
    for pattern in url_patterns:
        urls = re.findall(pattern, page_source)
        all_urls.extend(urls)
    
    # Remove duplicates and filter
    unique_urls = list(set(all_urls))
    valid_urls = [url for url in unique_urls if is_valid_search_url(url)]
    
    return valid_urls[:max_results]

def is_valid_search_url(url):
    """Check if URL is a valid search result (not an ad or internal page)"""
    if not url or not url.startswith('http'):
        return False
    
    # Filter out DuckDuckGo internal URLs
    duckduckgo_domains = [
        'duckduckgo.com',
        'start.duckduckgo.com',
        'links.duckduckgo.com'
    ]
    
    for domain in duckduckgo_domains:
        if domain in url:
            return False
    
    # Filter out obvious ad URLs
    ad_indicators = [
        'y.js',
        'ad_domain',
        'ad_provider',
        'click_metadata',
        'bing.com/aclick',
        'doubleclick.net',
        'googleadservices.com',
        'googlesyndication.com'
    ]
    
    for indicator in ad_indicators:
        if indicator in url:
            return False
    
    # Filter out extremely long URLs (likely tracking URLs)
    if len(url) > 1000:
        return False
    
    # Must be a reasonable length
    if len(url) < 15:
        return False
    
    # Allow URLs with common domains
    common_domains = [
        'wikipedia.org', 'tripadvisor.com', 'booking.com', 'expedia.com',
        'lonelyplanet.com', 'timeout.com', 'culturetrip.com', 'theculturetrip.com',
        'holidify.com', 'myfitour.com', 'vrogue.co', 'royalresidencies.com',
        'trip.com', 'getyourguide.com', 'viator.com', 'kayak.com',
        'google.com', 'yahoo.com', 'bing.com', 'reddit.com',
        'facts.net', 'worldblaze.in', 'leverageedu.com', 'rd.com',
        'ranker.com', 'bestlifeonline.com', 'thrillophilia.com', 'wanderon.in',
        'blissfulbihar.com'
    ]
    
    # If it contains a common domain, it's likely valid
    for domain in common_domains:
        if domain in url:
            return True
    
    # For other URLs, be more lenient
    return True

if __name__ == "__main__":
    # Test the search functionality
    query = input("Enter search query: ")
    num_results = int(input("Enter number of results (default 5): ") or "5")
    
    urls = search_duckduckgo(query, num_results)
    
    print(f"\nFinal Search Results:")
    print("=" * 50)
    for i, url in enumerate(urls, 1):
        print(f"{i}. {url}")
    
    if not urls:
        print("No URLs found. This might be due to:")
        print("- DuckDuckGo blocking automated requests")
        print("- Network connectivity issues")
        print("- Search query returning no results")
        print("- URL filtering being too strict") 