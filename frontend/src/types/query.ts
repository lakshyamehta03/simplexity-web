
export interface Source {
  title: string;
  url: string;
  snippet: string;
  domain: string;
}

export interface QueryResult {
  originalQuery: string;
  isValid: boolean;
  fromCache: boolean;
  summary: string;
  sources: Source[];
  processingTime: number;
  timestamp: Date;
  similarityScore?: number;
}

export interface ProcessingStep {
  id: string;
  name: string;
  description: string;
  completed: boolean;
}
