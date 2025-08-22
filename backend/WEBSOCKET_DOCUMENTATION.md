# Backend WebSocket Implementation Documentation

## Overview

The backend WebSocket implementation provides real-time status updates during query processing. It uses FastAPI's WebSocket support to maintain persistent connections with frontend clients and emit pipeline step updates as queries are processed.

## Architecture

### WSManager Class

Location: `backend/main.py` (lines 80-110)

The `WSManager` class handles WebSocket connection management:

```python
class WSManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        ws_logger.info("WSManager initialized")

    async def connect(self, websocket: WebSocket, ws_id: str):
        # Accepts WebSocket connection and stores it
        
    async def disconnect(self, ws_id: str):
        # Removes WebSocket connection from active connections
        
    async def send_message(self, ws_id: str, message: dict):
        # Sends JSON message to specific WebSocket connection
```

**Key Features:**
- Maintains a dictionary of active WebSocket connections indexed by `ws_id`
- Handles connection lifecycle (connect/disconnect)
- Provides message sending with error handling
- Comprehensive logging for debugging

### WebSocket Endpoints

#### 1. Status WebSocket Endpoint

**Endpoint:** `/ws/status/{ws_id}`  
**Location:** `backend/main.py` (lines 365-431)

```python
@app.websocket("/ws/status/{ws_id}")
async def websocket_status(websocket: WebSocket, ws_id: str):
```

**Functionality:**
- Accepts WebSocket connections for real-time status updates
- Sends initial "connected" message upon connection
- Implements keep-alive mechanism with ping messages every 30 seconds
- Handles client messages and connection cleanup
- Comprehensive logging of connection lifecycle

**Message Flow:**
1. Client connects to `/ws/status/{ws_id}`
2. Server sends `{"type": "connected", "message": "WebSocket connected"}`
3. Server periodically sends `{"type": "ping"}` messages
4. Server receives status updates from query processing pipeline
5. Server forwards status updates to connected client

#### 2. Query Processing Endpoint

**Endpoint:** `/query/stream/{ws_id}`  
**Location:** `backend/main.py` (lines 432-480)

```python
@app.post("/query/stream/{ws_id}")
async def process_query_stream(request: QueryRequest, ws_id: str):
```

**Functionality:**
- Processes queries with real-time status updates
- Uses `sync_callback` function to emit status updates via WebSocket
- Handles both synchronous and asynchronous execution contexts
- Returns complete query results after processing

### Status Update Mechanism

#### sync_callback Function

**Location:** `backend/main.py` (lines 481-500)

```python
def sync_callback(step: str, ws_id: str):
    """Callback function to emit status updates from synchronous query processing"""
```

**Key Features:**
- Bridges synchronous query processing with asynchronous WebSocket communication
- Detects if an event loop is already running
- Uses `asyncio.ensure_future()` for running loops
- Falls back to `asyncio.run()` for new loops
- Comprehensive error handling and logging

**Status Update Flow:**
1. Query processor calls `sync_callback(step, ws_id)`
2. Function determines appropriate asyncio execution method
3. Schedules `manager.send_message()` coroutine
4. WebSocket manager sends status update to connected client
5. Frontend receives and processes status update

## Pipeline Steps

The following pipeline steps are emitted during query processing:

| Step | Description | Frontend Mapping |
|------|-------------|------------------|
| `validating` | Query validation | `validating` |
| `similarity` | Cache similarity check | `similarity` |
| `cache_hit` | Cache hit found | `similarity` |
| `searching` | Web search execution | `searching` |
| `scraping` | Content extraction | `scraping` |
| `summarizing` | AI summary generation | `summarizing` |
| `done` | Processing complete | `summarizing` |

## Logging

Comprehensive logging is implemented throughout the WebSocket system:

### Logger Configuration
```python
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ws_logger = logging.getLogger('websocket')
ws_logger.setLevel(logging.INFO)
```

### Log Categories
- **INFO**: Connection events, status updates, query processing milestones
- **DEBUG**: Message details, ping/pong, successful operations
- **ERROR**: Connection failures, message sending errors, exceptions
- **WARNING**: Attempts to operate on non-existent connections

## Error Handling

### Connection Errors
- WebSocket disconnections are logged and handled gracefully
- Failed message sends are logged with error details
- Cleanup ensures no orphaned connections remain

### Processing Errors
- Query processing errors don't break WebSocket connections
- Status updates continue even if individual steps fail
- Comprehensive error logging for debugging

## Usage Example

```python
# 1. Frontend connects to WebSocket
ws = new WebSocket('ws://localhost:8000/ws/status/abc123');

# 2. Frontend sends query to streaming endpoint
fetch('http://localhost:8000/query/stream/abc123', {
  method: 'POST',
  body: JSON.stringify({ query: 'What is machine learning?' })
});

# 3. Backend processes query and emits status updates
sync_callback('validating', 'abc123')  # -> WebSocket message
sync_callback('searching', 'abc123')   # -> WebSocket message
sync_callback('scraping', 'abc123')    # -> WebSocket message
sync_callback('summarizing', 'abc123') # -> WebSocket message
sync_callback('done', 'abc123')        # -> WebSocket message

# 4. Frontend receives real-time updates and animates UI
```

## Configuration

### Environment Variables
- No specific WebSocket configuration required
- Uses FastAPI default WebSocket settings
- Logging level can be adjusted via `logging` configuration

### Performance Considerations
- WebSocket connections are lightweight and efficient
- Keep-alive pings prevent connection timeouts
- Automatic cleanup prevents memory leaks
- Logging can be adjusted for production environments

## Troubleshooting

### Common Issues
1. **Connection Refused**: Ensure backend server is running on correct port
2. **No Status Updates**: Check `sync_callback` is being called during processing
3. **Connection Drops**: Review network stability and keep-alive settings
4. **Memory Leaks**: Verify WebSocket cleanup in `finally` blocks

### Debug Steps
1. Enable DEBUG logging: `ws_logger.setLevel(logging.DEBUG)`
2. Monitor WebSocket connection logs
3. Check query processing pipeline calls to `sync_callback`
4. Verify frontend WebSocket message handling

## Security Considerations

- WebSocket connections are not authenticated (suitable for development)
- Consider adding authentication for production deployments
- CORS is configured to allow frontend connections
- No sensitive data is transmitted via WebSocket messages