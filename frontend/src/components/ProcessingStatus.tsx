import React, { useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { CheckCircle, Circle, Loader2 } from 'lucide-react';

// Processing status logging utility
const statusLog = {
  info: (message: string, data?: any) => {
    const timestamp = new Date().toISOString();
    console.log(`[STATUS-INFO ${timestamp}] ${message}`, data || '');
  },
  debug: (message: string, data?: any) => {
    const timestamp = new Date().toISOString();
    console.debug(`[STATUS-DEBUG ${timestamp}] ${message}`, data || '');
  }
};

interface ProcessingStatusProps {
  currentStep: string;
  query: string;
}

export const ProcessingStatus: React.FC<ProcessingStatusProps> = ({ currentStep, query }) => {
  const steps = [
    { id: 'validating', name: 'Validating Query', description: 'Checking if query is searchable' },
    { id: 'similarity', name: 'Checking Cache', description: 'Looking for similar past queries' },
    { id: 'searching', name: 'Web Search', description: 'Finding relevant web sources' },
    { id: 'scraping', name: 'Content Extraction', description: 'Extracting content from sources' },
    { id: 'summarizing', name: 'AI Analysis', description: 'Generating comprehensive summary' }
  ];

  const getCurrentStepIndex = () => {
    return steps.findIndex(step => step.id === currentStep);
  };

  const currentStepIndex = getCurrentStepIndex();

  // Log step changes and animations
  useEffect(() => {
    if (currentStep) {
      statusLog.info('Processing step changed', { 
        currentStep, 
        stepIndex: currentStepIndex, 
        stepName: steps[currentStepIndex]?.name || 'Unknown',
        query 
      });
      
      // Log animation state for each step
      steps.forEach((step, index) => {
        const isCompleted = index < currentStepIndex;
        const isCurrent = index === currentStepIndex;
        const isPending = index > currentStepIndex;
        
        if (isCompleted) {
          statusLog.debug(`Step completed: ${step.name}`, { stepId: step.id, index });
        } else if (isCurrent) {
          statusLog.info(`Step active with spinning animation: ${step.name}`, { stepId: step.id, index });
        } else if (isPending) {
          statusLog.debug(`Step pending: ${step.name}`, { stepId: step.id, index });
        }
      });
    }
  }, [currentStep, currentStepIndex, query]);

  return (
    <Card className="p-6 bg-white/70 backdrop-blur-sm border-0 shadow-xl">
      <div className="text-center mb-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-2">Processing Your Query</h3>
        <p className="text-gray-600 italic">"{query}"</p>
      </div>

      <div className="space-y-4">
        {steps.map((step, index) => {
          const isCompleted = index < currentStepIndex;
          const isCurrent = index === currentStepIndex;
          const isPending = index > currentStepIndex;

          // Only the current step gets the spinner animation
          // Completed steps get a checkmark, pending steps get a gray circle
          return (
            <div key={step.id} className="flex items-center space-x-3">
              <div className="flex-shrink-0">
                {isCompleted && (
                  <CheckCircle className="w-6 h-6 text-green-500" />
                )}
                {isCurrent && (
                  <Loader2 className="w-6 h-6 text-blue-500 animate-spin" />
                )}
                {isPending && (
                  <Circle className="w-6 h-6 text-gray-300" />
                )}
              </div>
              
              <div className="flex-grow">
                <div className={`font-medium ${
                  isCompleted ? 'text-green-700' : 
                  isCurrent ? 'text-blue-700' : 
                  'text-gray-400'
                }`}>
                  {step.name}
                </div>
                <div className={`text-sm ${
                  isCompleted ? 'text-green-600' : 
                  isCurrent ? 'text-blue-600' : 
                  'text-gray-400'
                }`}>
                  {step.description}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-6">
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div 
            className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full transition-all duration-300"
            style={{ width: `${((currentStepIndex + 1) / steps.length) * 100}%` }}
          ></div>
        </div>
      </div>
    </Card>
  );
};
