const API_BASE_URL = 'http://localhost:8000';

export interface QueryRequest {
  query: string;
}

export interface QueryResponse {
  valid: boolean;
  is_valid: boolean;
  is_time_sensitive: boolean;
  summary: string | null;
  from_cache: boolean;
  cached_query: string | null;
  urls_found: number;
  content_scraped: number;
  scraped_urls: string[];
  processing_time: number;
  search_time: number;
  scrape_time: number;
  cache_similarity: number;
  error?: string;
}

export interface CacheStats {
  cache_count: number;
  cached_queries: string[];
}

class ApiService {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  async query(request: QueryRequest): Promise<QueryResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('API query error:', error);
      throw error;
    }
  }

  async classify(request: QueryRequest): Promise<{ valid: boolean }> {
    try {
      const response = await fetch(`${this.baseUrl}/classify`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('API classify error:', error);
      throw error;
    }
  }

  async getCacheStats(): Promise<CacheStats> {
    try {
      const response = await fetch(`${this.baseUrl}/cache/stats`);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('API cache stats error:', error);
      throw error;
    }
  }

  async clearCache(): Promise<{ message: string }> {
    try {
      const response = await fetch(`${this.baseUrl}/cache/clear`, {
        method: 'POST',
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('API clear cache error:', error);
      throw error;
    }
  }

  async healthCheck(): Promise<{ status: string; message: string }> {
    try {
      const response = await fetch(`${this.baseUrl}/health`);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('API health check error:', error);
      throw error;
    }
  }
}

export const apiService = new ApiService();