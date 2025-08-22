import { QueryResult, Source } from '../types/query';
import { apiService, QueryResponse } from './api';

// Helper function to create sources based on backend response
const createSources = (scrapedUrls: string[]): Source[] => {
  if (!scrapedUrls || scrapedUrls.length === 0) return [];
  
  return scrapedUrls.map((url, index) => {
    const domain = new URL(url).hostname;
    return {
      title: `Source ${index + 1} - ${domain}`,
      url: url,
      snippet: `Content scraped from ${domain}`,
      domain: domain
    };
  });
};

export const queryProcessor = async (
  query: string,
  onStepChange: (step: string) => void
): Promise<QueryResult> => {
  const startTime = Date.now();
  
  try {
    // Step 1: Validate Query (this happens on the backend, but we show the step)
  onStepChange('validating');
  
    // Step 2: Check Similarity/Cache (this also happens on the backend)
  onStepChange('similarity');
  
    // Step 3: Make the API call (backend handles all steps internally)
    onStepChange('searching');
    
    const response: QueryResponse = await apiService.query({ query });
  
    // Step 4: Processing complete
  onStepChange('summarizing');
  
  const processingTime = Date.now() - startTime;
  
    // Map backend response to frontend format
    const result: QueryResult = {
      originalQuery: query,
      valid: response.valid,
      is_valid: response.is_valid,
      is_time_sensitive: response.is_time_sensitive,
      fromCache: response.from_cache,
      cachedQuery: response.cached_query || undefined,
      summary: response.summary || "No summary available",
      sources: createSources(response.scraped_urls || []),
      processingTime: response.processing_time * 1000, // Convert to milliseconds
      timestamp: new Date(),
      similarityScore: response.cache_similarity,
      urlsFound: response.urls_found,
      contentScraped: response.content_scraped,
      searchTime: response.search_time,
      scrapeTime: response.scrape_time,
      cacheSimilarity: response.cache_similarity
    };
    
    return result;
    
  } catch (error) {
    console.error('Query processing failed:', error);
    
    // Return error result
  return {
    originalQuery: query,
      valid: false,
      is_valid: false,
      is_time_sensitive: false,
      fromCache: false,
      summary: `Error: ${error instanceof Error ? error.message : 'Unknown error occurred'}`,
      sources: [],
      processingTime: Date.now() - startTime,
    timestamp: new Date(),
      similarityScore: 0
  };
  }
};
