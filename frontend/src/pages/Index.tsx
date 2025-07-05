import React, { useState } from 'react';
import { QueryInput } from '../components/QueryInput';
import { QueryResults } from '../components/QueryResults';
import { ProcessingStatus } from '../components/ProcessingStatus';
import { QueryHistory } from '../components/QueryHistory';
import { Header } from '../components/Header';
import { queryProcessor } from '../utils/queryProcessor';
import { QueryResult } from '../types/query';

const Index = () => {
  const [currentQuery, setCurrentQuery] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingStep, setProcessingStep] = useState('');
  const [results, setResults] = useState<QueryResult | null>(null);
  const [queryHistory, setQueryHistory] = useState<QueryResult[]>([]);

  const handleQuerySubmit = async (query: string) => {
    setCurrentQuery(query);
    setIsProcessing(true);
    setResults(null);

    try {
      const result = await queryProcessor(query, setProcessingStep);
      setResults(result);
      setQueryHistory(prev => [result, ...prev.slice(0, 4)]);
    } catch (error) {
      console.error('Query processing failed:', error);
    } finally {
      setIsProcessing(false);
      setProcessingStep('');
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
              Ripplica Query Agent
            </h1>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              Intelligent web browser query agent that validates, searches, and summarizes information from the web
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
