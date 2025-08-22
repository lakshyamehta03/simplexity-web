# Frontend WebSocket Implementation Documentation

## Overview

The frontend WebSocket implementation provides real-time status updates during query processing. It connects to the backend WebSocket endpoint and updates the UI with pipeline step progress, including animated spinning circles for active steps.

## Architecture

### Core Components

#### 1. WebSocket Utility (`src/utils/socket.ts`)

The main WebSocket connection handler that manages communication with the backend.

```typescript
export function connectStatusSocket(
  wsId: string, 
  onStatusUpdate: (event: StatusEvent) => void
): WebSocket
```

**Key Features:**
- Establishes WebSocket connection to backend
- Handles message parsing and filtering
- Provides comprehensive logging
- Manages connection lifecycle

#### 2. Query Processing (`src/pages/Index.tsx`)

The main page component that orchestrates query submission and WebSocket connections.

**Key Features:**
- Generates unique WebSocket IDs
- Connects to status WebSocket before query submission
- Maps backend status events to UI steps
- Handles query processing lifecycle

#### 3. Processing Status UI (`src/components/ProcessingStatus.tsx`)

The UI component that displays pipeline steps with animations.

**Key Features:**
- Displays pipeline steps with visual indicators
- Animates spinning circles for active steps
- Shows completed steps with checkmarks
- Logs step changes and animation states

## WebSocket Connection Flow

### 1. Connection Establishment

```typescript
// Generate unique WebSocket ID
const wsId = Math.random().toString(36).slice(2);

// Connect to WebSocket endpoint
wsRef.current = connectStatusSocket(wsId, (evt) => {
  const step = mapStep(evt);
  setProcessingStep(step);
});
```

### 2. Message Handling

```typescript
websocket.onmessage = (event) => {
  try {
    const data = JSON.parse(event.data) as StatusEvent;
    
    // Filter out system messages
    if (data.type === 'ping' || data.type === 'connected') {
      return;
    }
    
    // Process status updates
    onStatusUpdate(data);
  } catch (error) {
    wsLog.error('Failed to parse WebSocket message', error);
  }
};
```

### 3. Connection Cleanup

```typescript
finally {
  setIsProcessing(false);
  setProcessingStep('');
  if (wsRef.current) {
    wsRef.current.close();
    wsRef.current = null;
  }
}
```

## Status Event Types

### StatusEvent Interface

```typescript
interface StatusEvent {
  step: string;
  type?: 'connected' | 'ping' | 'status';
  message?: string;
}
```

### Backend to Frontend Step Mapping

```typescript
const mapStep = (evt: StatusEvent): string => {
  switch (evt.step) {
    case 'classifying':
    case 'validating':
      return 'validating';
    case 'similarity':
    case 'cache_hit':
      return 'similarity';
    case 'searching':
      return 'searching';
    case 'scraping':
      return 'scraping';
    case 'summarizing':
    case 'done':
    default:
      return 'summarizing';
  }
};
```

## UI Animation System

### Pipeline Steps Configuration

```typescript
const steps = [
  { id: 'validating', name: 'Validating Query', description: 'Checking if query is searchable' },
  { id: 'similarity', name: 'Checking Cache', description: 'Looking for similar past queries' },
  { id: 'searching', name: 'Web Search', description: 'Finding relevant web sources' },
  { id: 'scraping', name: 'Content Extraction', description: 'Extracting content from sources' },
  { id: 'summarizing', name: 'AI Analysis', description: 'Generating comprehensive summary' }
];
```

### Animation States

| State | Visual Indicator | CSS Class | Description |
|-------|------------------|-----------|-------------|
| **Completed** | ✅ CheckCircle | `text-green-500` | Step finished successfully |
| **Active** | 🔄 Loader2 | `text-blue-500 animate-spin` | Currently processing with spinning animation |
| **Pending** | ⭕ Circle | `text-gray-300` | Waiting to be processed |

### Animation Logic

```typescript
const isCompleted = index < currentStepIndex;
const isCurrent = index === currentStepIndex;
const isPending = index > currentStepIndex;

// Render appropriate icon based on state
{isCompleted && <CheckCircle className="w-6 h-6 text-green-500" />}
{isCurrent && <Loader2 className="w-6 h-6 text-blue-500 animate-spin" />}
{isPending && <Circle className="w-6 h-6 text-gray-300" />}
```

## Logging System

### WebSocket Logging (`src/utils/socket.ts`)

```typescript
const wsLog = {
  info: (message: string, data?: any) => {
    const timestamp = new Date().toISOString();
    console.log(`[WS-INFO ${timestamp}] ${message}`, data || '');
  },
  error: (message: string, error?: any) => {
    const timestamp = new Date().toISOString();
    console.error(`[WS-ERROR ${timestamp}] ${message}`, error || '');
  },
  debug: (message: string, data?: any) => {
    const timestamp = new Date().toISOString();
    console.debug(`[WS-DEBUG ${timestamp}] ${message}`, data || '');
  }
};
```

### Query Processing Logging (`src/pages/Index.tsx`)

```typescript
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
```

### Status Animation Logging (`src/components/ProcessingStatus.tsx`)

```typescript
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
```

## Complete Query Processing Flow

### 1. Query Submission
```typescript
// User submits query
queryLog.info('Starting query submission', { query, timestamp: Date.now() });

// Generate WebSocket ID
const wsId = Math.random().toString(36).slice(2);
queryLog.info('Generated WebSocket ID', { wsId });
```

### 2. WebSocket Connection
```typescript
// Connect to WebSocket
queryLog.debug('Connecting to WebSocket for status updates');
wsRef.current = connectStatusSocket(wsId, (evt) => {
  queryLog.info('Received status event from WebSocket', { event: evt, wsId });
  const step = mapStep(evt);
  setProcessingStep(step);
  queryLog.debug('Updated processing step in UI', { step });
});
```

### 3. Backend Query Processing
```typescript
// Send query to backend
queryLog.info('Sending query to backend streaming endpoint', { wsId, endpoint: `/query/stream/${wsId}` });
const response = await fetch(`http://localhost:8000/query/stream/${wsId}`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ query })
});
```

### 4. Real-time Status Updates
```typescript
// Backend sends status updates via WebSocket
// Frontend receives and processes updates
// UI animations update automatically

// Example status update flow:
// 1. Backend: sync_callback('validating', wsId)
// 2. WebSocket: {"step": "validating"}
// 3. Frontend: mapStep() -> 'validating'
// 4. UI: Spinning circle on "Validating Query" step
```

### 5. Completion and Cleanup
```typescript
// Query processing completes
queryLog.info('Query processing completed successfully', { 
  valid: result.valid, 
  fromCache: result.fromCache, 
  processingTime: result.processingTime 
});

// Cleanup WebSocket connection
queryLog.info('Cleaning up query processing', { wsId });
if (wsRef.current) {
  queryLog.debug('Closing WebSocket connection');
  wsRef.current.close();
  wsRef.current = null;
}
```

## Error Handling

### WebSocket Connection Errors
```typescript
websocket.onerror = (error) => {
  wsLog.error('WebSocket connection error', error);
};

websocket.onclose = (event) => {
  const duration = Date.now() - connectionStart;
  wsLog.info('WebSocket connection closed', {
    code: event.code,
    reason: event.reason,
    wasClean: event.wasClean,
    duration: `${duration}ms`,
    messagesReceived,
    pingsReceived
  });
};
```

### Query Processing Errors
```typescript
try {
  // Query processing logic
} catch (error) {
  queryLog.error('Query processing failed', error);
  console.error('Query processing failed:', error);
} finally {
  // Always cleanup WebSocket connection
  queryLog.info('Cleaning up query processing', { wsId });
  // ... cleanup logic
}
```

## Performance Considerations

### Connection Management
- WebSocket connections are created per query and cleaned up automatically
- Only one WebSocket connection is active at a time per query
- Connections are closed immediately after query completion

### Message Filtering
- System messages (`ping`, `connected`) are filtered out from UI updates
- Only relevant status updates trigger UI re-renders
- Logging can be disabled in production for performance

### Animation Optimization
- CSS animations are hardware-accelerated (`animate-spin`)
- Only the current step shows spinning animation
- Completed and pending steps use static icons

## Troubleshooting

### Common Issues

1. **No Status Updates**
   - Check WebSocket connection in browser DevTools
   - Verify backend WebSocket endpoint is running
   - Check console logs for connection errors

2. **Animation Not Working**
   - Verify `currentStep` state is updating
   - Check step mapping logic
   - Ensure Tailwind CSS classes are loaded

3. **Connection Drops**
   - Check network connectivity
   - Verify backend keep-alive pings
   - Review WebSocket close event logs

### Debug Steps

1. **Enable Debug Logging**
   ```typescript
   // Temporarily change console.debug to console.log
   console.debug = console.log;
   ```

2. **Monitor WebSocket in DevTools**
   - Open Browser DevTools → Network → WS
   - Monitor WebSocket connection and messages

3. **Check Component State**
   ```typescript
   // Add temporary logging
   console.log('Current step:', currentStep);
   console.log('Step index:', currentStepIndex);
   ```

## Configuration

### WebSocket Endpoint
```typescript
// Default configuration
const WS_BASE_URL = 'ws://localhost:8000';
const WS_ENDPOINT = `/ws/status/${wsId}`;
```

### Logging Levels
```typescript
// Production: Disable debug logging
if (process.env.NODE_ENV === 'production') {
  console.debug = () => {};
}
```

### Animation Timing
```css
/* Tailwind CSS animation classes */
.animate-spin {
  animation: spin 1s linear infinite;
}
```

## Integration Example

```typescript
// Complete integration example
const handleQuerySubmit = async (query: string) => {
  // 1. Setup
  const wsId = Math.random().toString(36).slice(2);
  setIsProcessing(true);
  
  // 2. Connect WebSocket
  wsRef.current = connectStatusSocket(wsId, (evt) => {
    const step = mapStep(evt);
    setProcessingStep(step); // Triggers UI animation
  });
  
  // 3. Submit query
  try {
    const response = await fetch(`/query/stream/${wsId}`, {
      method: 'POST',
      body: JSON.stringify({ query })
    });
    const result = await response.json();
    setResults(result);
  } finally {
    // 4. Cleanup
    setIsProcessing(false);
    wsRef.current?.close();
  }
};
```