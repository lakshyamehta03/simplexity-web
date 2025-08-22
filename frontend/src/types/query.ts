
export interface Source {
  title: string;
  url: string;
  snippet: string;
  domain: string;
}

export interface QueryResult {
  originalQuery: string;
  valid: boolean;
  is_valid: boolean;
  is_time_sensitive: boolean;
  fromCache: boolean;
  cachedQuery?: string;
  summary: string;
  sources: Source[];
  processingTime: number;
  timestamp: Date;
  similarityScore?: number;
  urlsFound?: number;
  contentScraped?: number;
  searchTime?: number;
  scrapeTime?: number;
  cacheSimilarity?: number;
}

export interface ProcessingStep {
  id: string;
  name: string;
  description: string;
  completed: boolean;
}
