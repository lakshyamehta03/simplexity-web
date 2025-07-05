
import React from 'react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ExternalLink, Clock, CheckCircle, Database } from 'lucide-react';
import { QueryResult } from '../types/query';

interface QueryResultsProps {
  result: QueryResult;
}

export const QueryResults: React.FC<QueryResultsProps> = ({ result }) => {
  return (
    <div className="space-y-6">
      {/* Query Status */}
      <Card className="p-6 bg-white/70 backdrop-blur-sm border-0 shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-gray-800">Query Results</h2>
          <div className="flex items-center space-x-4">
            <Badge variant={result.fromCache ? "secondary" : "default"} className="flex items-center space-x-1">
              {result.fromCache ? <Database className="w-3 h-3" /> : <CheckCircle className="w-3 h-3" />}
              <span>{result.fromCache ? 'From Cache' : 'Fresh Results'}</span>
            </Badge>
            <div className="flex items-center text-sm text-gray-500">
              <Clock className="w-4 h-4 mr-1" />
              {result.processingTime}ms
            </div>
          </div>
        </div>

        <div className="bg-blue-50 border-l-4 border-blue-400 p-4 rounded-r-lg">
          <p className="text-blue-800 font-medium">"{result.originalQuery}"</p>
          <p className="text-blue-600 text-sm mt-1">
            {result.isValid ? 'Valid search query' : 'Invalid query type'}
          </p>
        </div>
      </Card>

      {/* Main Summary */}
      <Card className="p-6 bg-white/70 backdrop-blur-sm border-0 shadow-xl">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Summary</h3>
        <div className="prose prose-gray max-w-none">
          <p className="text-gray-700 leading-relaxed whitespace-pre-line">
            {result.summary}
          </p>
        </div>
      </Card>

      {/* Sources */}
      <Card className="p-6 bg-white/70 backdrop-blur-sm border-0 shadow-xl">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Sources</h3>
        <div className="grid gap-4">
          {result.sources.map((source, index) => (
            <div key={index} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors">
              <div className="flex items-start justify-between">
                <div className="flex-grow">
                  <h4 className="font-medium text-gray-800 mb-1">{source.title}</h4>
                  <p className="text-sm text-gray-600 mb-2 line-clamp-2">{source.snippet}</p>
                  <p className="text-xs text-gray-500">{source.domain}</p>
                </div>
                <a
                  href={source.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="ml-4 p-2 text-blue-500 hover:text-blue-700 hover:bg-blue-50 rounded-lg transition-colors"
                >
                  <ExternalLink className="w-4 h-4" />
                </a>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
};
