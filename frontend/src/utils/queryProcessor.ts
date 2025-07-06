import { QueryResult, Source } from '../types/query';
import { apiService, QueryResponse } from './api';

// Helper function to create sources based on backend response
const createSources = (urlsFound: number, contentScraped: number): Source[] => {
  if (urlsFound === 0) return [];
  
  return [
  {
      title: "Web Search Results",
      url: "https://search-results.com",
      snippet: `Found ${urlsFound} URLs and scraped content from ${contentScraped} pages.`,
      domain: "search-results.com"
  },
  {
      title: "AI Summarization",
      url: "https://ai-summary.com", 
      snippet: "Content was analyzed and summarized using the LED-large AI model.",
      domain: "ai-summary.com"
  }
];
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
      isValid: response.valid,
      fromCache: response.from_cache,
      summary: response.summary || "No summary available",
      sources: createSources(response.urls_found, response.content_scraped),
      processingTime: response.processing_time * 1000, // Convert to milliseconds
      timestamp: new Date(),
      similarityScore: response.cache_similarity
    };
    
    return result;
    
  } catch (error) {
    console.error('Query processing failed:', error);
    
    // Return error result
  return {
    originalQuery: query,
      isValid: false,
      fromCache: false,
      summary: `Error: ${error instanceof Error ? error.message : 'Unknown error occurred'}`,
      sources: [],
      processingTime: Date.now() - startTime,
    timestamp: new Date(),
      similarityScore: 0
  };
  }
};
