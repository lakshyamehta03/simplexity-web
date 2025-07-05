
import React from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { History, RefreshCw } from 'lucide-react';
import { QueryResult } from '../types/query';

interface QueryHistoryProps {
  history: QueryResult[];
  onSelectQuery: (query: string) => void;
}

export const QueryHistory: React.FC<QueryHistoryProps> = ({ history, onSelectQuery }) => {
  return (
    <Card className="p-6 bg-white/70 backdrop-blur-sm border-0 shadow-xl">
      <div className="flex items-center space-x-2 mb-4">
        <History className="w-5 h-5 text-gray-600" />
        <h3 className="text-lg font-semibold text-gray-800">Recent Queries</h3>
      </div>

      <div className="space-y-3">
        {history.map((result, index) => (
          <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
            <div className="flex-grow">
              <p className="font-medium text-gray-800 text-sm truncate">
                {result.originalQuery}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                {result.fromCache ? 'Cached result' : 'Fresh search'} • {result.processingTime}ms
              </p>
            </div>
            <Button
              onClick={() => onSelectQuery(result.originalQuery)}
              variant="ghost"
              size="sm"
              className="ml-2"
            >
              <RefreshCw className="w-4 h-4" />
            </Button>
          </div>
        ))}
      </div>
    </Card>
  );
};
