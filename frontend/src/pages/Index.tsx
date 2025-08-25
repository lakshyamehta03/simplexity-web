import React, { useState, useRef } from 'react';
import { QueryInput } from '../components/QueryInput';
import { QueryResults } from '../components/QueryResults';
import { ProcessingStatus } from '../components/ProcessingStatus';
import { QueryHistory } from '../components/QueryHistory';
import { Header } from '../components/Header';
import { queryProcessor } from '../utils/queryProcessor';
import { QueryResult } from '../types/query';
import { connectStatusSocket, StatusEvent } from '../utils/socket';

// Query processing logging utility
const queryLog = {
  info: (message: string, data?: any) => {
    const timestamp = new Date().toISOString();
    console.log(`[QUERY-INFO ${timestamp}] ${message}`, data || '');
  },
  error: (message: string, error?: any) => {
    const timestamp = new Date().toISOString();
    console.error(`[QUERY-ERROR ${timestamp}] ${message}`, error || '');
  },
  debug: (message: string, data?: any) => {
    const timestamp = new Date().toISOString();
    console.debug(`[QUERY-DEBUG ${timestamp}] ${message}`, data || '');
  }
};

const Index = () => {
  const [currentQuery, setCurrentQuery] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingStep, setProcessingStep] = useState('');
  const [results, setResults] = useState<QueryResult | null>(null);
  const [queryHistory, setQueryHistory] = useState<QueryResult[]>([]);
  const wsRef = useRef<WebSocket | null>(null);

  const mapStep = (evt: StatusEvent): string => {
    queryLog.debug('Mapping status event to UI step', { originalStep: evt.step, eventData: evt });
    
    let mappedStep: string;
    switch (evt.step) {
      case 'validating':
        mappedStep = 'validating';
        break;
      case 'similarity':
      case 'cache_hit':
        mappedStep = 'similarity';
        break;
      case 'searching':
        mappedStep = 'searching';
        break;
      case 'scraping':
        mappedStep = 'scraping';
        break;
      case 'summarizing':
        mappedStep = 'summarizing';
        break;
      case 'done':
      default:
        mappedStep = 'summarizing';
        break;
    }
    
    queryLog.info(`Step mapped: ${evt.step} -> ${mappedStep}`);
    return mappedStep;
  };

  const handleQuerySubmit = async (query: string) => {
    queryLog.info('Starting query submission', { query, timestamp: Date.now() });
    
    setCurrentQuery(query);
    setIsProcessing(true);
    setResults(null);

    // Generate a ws id
    const wsId = Math.random().toString(36).slice(2);
    queryLog.info('Generated WebSocket ID', { wsId });
    
    // Connect websocket
    queryLog.debug('Connecting to WebSocket for status updates');
    wsRef.current = connectStatusSocket(wsId, (evt) => {
      queryLog.info('Received status event from WebSocket', { event: evt, wsId });
      const step = mapStep(evt);
      setProcessingStep(step);
      queryLog.debug('Updated processing step in UI', { step });
    });

    try {
      // Use streaming endpoint so backend emits status updates
      queryLog.info('Sending query to backend streaming endpoint', { wsId, endpoint: `/query/stream/${wsId}` });
      const response = await fetch(`http://localhost:8000/query/stream/${wsId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query })
      });
      
      if (!response.ok) {
        queryLog.error('Backend response not OK', { status: response.status, statusText: response.statusText });
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      queryLog.info('Received response from backend', { data, processingTime: data.processing_time });
      
      // Add debug logging for scraped_urls
      console.log('DEBUG: Frontend received scraped_urls:', data.scraped_urls);
      console.log('DEBUG: Frontend scraped_urls count:', data.scraped_urls?.length || 0);
      
      // Fallback mapping to existing shape used by UI
      const result: QueryResult = {
        originalQuery: query,
        valid: data.valid,
        is_valid: data.is_valid,
        is_time_sensitive: data.is_time_sensitive,
        fromCache: data.from_cache,
        cachedQuery: data.cached_query || undefined,
        summary: data.summary || 'No summary available',
        sources: data.scraped_urls ? data.scraped_urls.map((url: string, index: number) => {
          const domain = new URL(url).hostname;
          return {
            title: `Source ${index + 1} - ${domain}`,
            url: url,
            snippet: `Content scraped from ${domain}`,
            domain: domain
          };
        }) : [],
        processingTime: (data.processing_time || 0) * 1000,
        timestamp: new Date(),
        similarityScore: data.cache_similarity,
        urlsFound: data.urls_found,
        contentScraped: data.content_scraped,
        searchTime: data.search_time,
        scrapeTime: data.scrape_time,
        cacheSimilarity: data.cache_similarity
      };

      queryLog.info('Query processing completed successfully', { 
        valid: result.valid, 
        fromCache: result.fromCache, 
        processingTime: result.processingTime 
      });
      
      setResults(result);
      setQueryHistory(prev => [result, ...prev.slice(0, 4)]);
      queryLog.debug('Updated UI with query results and history');
    } catch (error) {
      queryLog.error('Query processing failed', error);
      console.error('Query processing failed:', error);
    } finally {
      queryLog.info('Cleaning up query processing', { wsId });
      setIsProcessing(false);
      setProcessingStep('');
      if (wsRef.current) {
        queryLog.debug('Closing WebSocket connection');
        wsRef.current.close();
        wsRef.current = null;
      }
      queryLog.info('Query processing cleanup completed');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      <Header />
      
      <main className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto space-y-8">
          {/* Hero Section */}
          <div className="text-center space-y-4">
            <h1 className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              Simplexity
            </h1>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              Intelligent web browser query agent that searches and summarizes information from the web
            </p>
          </div>

          {/* Query Input */}
          <QueryInput 
            onSubmit={handleQuerySubmit} 
            isProcessing={isProcessing}
          />

          {/* Processing Status */}
          {isProcessing && (
            <ProcessingStatus 
              currentStep={processingStep}
              query={currentQuery}
            />
          )}

          {/* Results */}
          {results && !isProcessing && (
            <QueryResults result={results} />
          )}

          {/* Query History */}
          {queryHistory.length > 0 && (
            <QueryHistory 
              history={queryHistory}
              onSelectQuery={handleQuerySubmit}
            />
          )}
        </div>
      </main>
    </div>
  );
};

export default Index;
