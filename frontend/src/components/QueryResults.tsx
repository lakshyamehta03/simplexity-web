
import React from 'react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ExternalLink, Clock, CheckCircle, Database, Globe, Link } from 'lucide-react';
import { QueryResult } from '../types/query';
import ReactMarkdown from 'react-markdown';

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
            {result.is_valid ? 'Valid search query' : 'Invalid query type'}
            {result.is_time_sensitive && ' • Time-sensitive'}
            {result.fromCache && result.cachedQuery && (
              <span className="block mt-1 text-xs text-blue-500">
                Served from cache (original: "{result.cachedQuery}")
              </span>
            )}
          </p>
        </div>
      </Card>

      {/* Main Summary */}
      <Card className="p-6 bg-white/70 backdrop-blur-sm border-0 shadow-xl">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Summary</h3>
        <div className="prose prose-gray max-w-none">
          <div className="text-gray-700 leading-relaxed">
            <ReactMarkdown>{result.summary}</ReactMarkdown>
          </div>
        </div>
      </Card>

      {/* Enhanced Sources Section */}
      <Card className="p-6 bg-white/70 backdrop-blur-sm border-0 shadow-xl">
  <div className="flex items-center space-x-2 mb-6">
    <Globe className="w-5 h-5 text-blue-600" />
    <h3 className="text-lg font-semibold text-gray-800">Sources</h3>
    <Badge variant="outline" className="text-xs">
      {result.sources.length} {result.sources.length === 1 ? 'source' : 'sources'}
    </Badge>
  </div>
  
  {result.sources.length === 0 ? (
    <div className="text-center py-8 text-gray-500">
      <Globe className="w-12 h-12 mx-auto mb-3 opacity-50" />
      <p>No sources available for this query</p>
    </div>
  ) : (
    <div className="grid gap-4">
      {result.sources.map((source, index) => (
        <div
          key={index}
          className="group relative bg-gradient-to-r from-white to-gray-50 border border-gray-200 rounded-xl p-5 hover:shadow-lg hover:border-blue-300 transition-all duration-300 hover:-translate-y-1"
        >
          <div className="flex items-start space-x-4">
            {/* Domain Favicon */}
            <div className="flex-shrink-0">
              <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center shadow-md">
                <img 
                  src={`https://www.google.com/s2/favicons?domain=${source.domain}&sz=32`}
                  alt={`${source.domain} favicon`}
                  className="w-6 h-6 rounded"
                  onError={(e) => {
                    const target = e.target as HTMLImageElement;
                    target.style.display = 'none';
                    target.nextElementSibling?.classList.remove('hidden');
                  }}
                />
                <Globe className="w-6 h-6 text-white hidden" />
              </div>
            </div>
            {/* Content */}
            <div className="flex-grow min-w-0">
              <div className="flex items-start justify-between mb-2">
                <h4 className="font-semibold text-gray-900 text-base leading-tight group-hover:text-blue-700 transition-colors">
                  {source.title}
                </h4>
                <div className="flex items-center space-x-2 ml-4">
                  <Badge variant="secondary" className="text-xs px-2 py-1">
                    #{index + 1}
                  </Badge>
                </div>
              </div>
              <p className="text-sm text-gray-600 mb-3 line-clamp-2 leading-relaxed">
                {source.snippet}
              </p>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Link className="w-3 h-3 text-gray-400" />
                  <span className="text-xs text-gray-500 font-medium">{source.domain}</span>
                </div>
                <a
                  href={source.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center space-x-1 px-3 py-1.5 bg-blue-50 hover:bg-blue-100 text-blue-600 hover:text-blue-700 rounded-lg transition-all duration-200 text-sm font-medium group-hover:shadow-md"
                >
                  <span>Visit</span>
                  <ExternalLink className="w-3 h-3" />
                </a>
              </div>
            </div>
          </div>
                
                {/* Hover effect overlay */}
                <div className="absolute inset-0 bg-gradient-to-r from-blue-500/5 to-purple-500/5 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none" />
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
};
