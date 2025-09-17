# Ripplica Query Core System Explanation

This document provides a comprehensive explanation of the Ripplica Query Core system, including both frontend and backend components, and how they interact to process user queries.

## System Architecture Overview

Ripplica Query Core is a web application that allows users to input natural language queries, processes these queries through a sophisticated pipeline, and returns comprehensive summaries based on content scraped from the web. The system consists of two main components:

1. **Frontend**: A React-based user interface that handles user interactions and displays results
2. **Backend**: A FastAPI-based server that processes queries through a multi-stage pipeline

## Backend Architecture

The backend is built with Python using FastAPI as the web framework. It implements a modular architecture where each component handles a specific part of the query processing pipeline.

### Key Backend Components

#### 1. `main.py`

This is the entry point of the backend application. It:

- Sets up the FastAPI application with CORS middleware
- Defines API endpoints for query processing, cache management, and health checks
- Implements WebSocket connections for real-time status updates
- Defines Pydantic models for request/response validation

Key endpoints include:
- `/query`: Main endpoint for processing queries
- `/query/stream/{ws_id}`: Streaming version that sends status updates via WebSocket
- `/cache/*`: Endpoints for cache management (stats, clear, check, add)
- `/classify`: Endpoint for query classification

#### 2. `query_processor.py`

This is the core component that orchestrates the entire query processing pipeline. The `QueryProcessor` class implements a multi-step workflow:

1. **Query Validation**: Uses a classifier to determine if the query is valid and time-sensitive
2. **Cache Check**: For non-time-sensitive queries, checks if a similar query exists in the cache
3. **Web Search**: If no cache hit, searches the web for relevant content
4. **Content Scraping**: Extracts content from the search results
5. **Focused Extraction**: Extracts the most relevant parts of the scraped content
6. **Summarization**: Generates a comprehensive summary from the focused content
7. **Cache Storage**: Stores the results in the cache for future use

The processor also emits status updates throughout the pipeline via WebSockets.

#### 3. `content_scraper.py`

Handles the extraction of content from web pages. Key features:

- Uses Selenium with Chrome in headless mode for browser-based scraping
- Implements anti-bot detection measures
- Provides multiple scraping strategies (JavaScript disabled/enabled)
- Handles concurrent scraping of multiple URLs
- Includes error handling and fallback mechanisms

#### 4. `focused_extractor.py`

Extracts the most relevant content from scraped web pages based on the user's query:

- Supports multiple extraction methods:
  - TextRank algorithm for keyword-based extraction
  - Groq LLM for more sophisticated extraction
  - Fallback to simple keyword-based extraction
- Handles errors gracefully with fallback mechanisms

#### 5. `summarizer.py`

Generates comprehensive summaries from the focused content using Groq's LLM:

- Constructs detailed prompts that include the user's query and extracted content
- Uses the Groq API with the llama-3.3-70b-versatile model
- Formats responses in Markdown for better readability
- Includes system prompts to guide the LLM's response format

#### 6. `simplexity_classifier.py`

Classifies queries to determine if they are valid and time-sensitive:

- Uses LLM-based classification
- Supports multiple LLM providers (Groq, OpenAI)
- Returns structured classification results

#### 7. `db.py`

Manages the vector database for query caching:

- Uses Chroma DB for vector storage
- Implements similarity search for finding similar queries
- Handles embedding storage and retrieval

#### 8. `embeddings.py`

Generates embeddings for queries to enable similarity-based cache lookups:

- Uses embedding models to convert text to vector representations
- Supports caching of embeddings for performance

## Frontend Architecture

The frontend is built with React and TypeScript, using a component-based architecture.

### Key Frontend Components

#### 1. `Index.tsx`

The main page component that:

- Manages application state (current query, processing status, results)
- Handles WebSocket connections for real-time status updates
- Coordinates the interaction between child components

#### 2. `QueryInput.tsx`

Handles user input:

- Provides a search input field with validation
- Manages the submission of queries to the backend
- Shows loading state during processing

#### 3. `ProcessingStatus.tsx`

Displays the current status of query processing:

- Shows a step-by-step visualization of the pipeline
- Updates in real-time based on WebSocket messages
- Provides visual feedback on the current processing stage

#### 4. `QueryResults.tsx`

Displays the results of the query:

- Renders the summary using ReactMarkdown for proper Markdown formatting
- Shows metadata about the query (processing time, cache status)
- Displays source information when available

#### 5. `socket.ts`

Manages WebSocket connections for real-time status updates:

- Establishes connections to the backend WebSocket endpoint
- Processes incoming messages and forwards them to the appropriate components
- Handles connection lifecycle (open, message, close, error)

## System Flow Diagram

```
┌─────────────────┐                 ┌─────────────────────────────────────────────────────────────────────┐
│                 │                 │                                                                     │
│    Frontend     │                 │                          Backend                                   │
│                 │                 │                                                                     │
└────────┬────────┘                 └───────────────────────────────────┬─────────────────────────────────┘
         │                                                              │
         │                                                              │
         │                                                              │
┌────────▼────────┐                 ┌───────────────────────────────────▼─────────────────────────────────┐
│                 │                 │                                                                     │
│   User Query    │────────────────▶│                      Query Validation                              │
│                 │                 │                 (simplexity_classifier.py)                         │
└─────────────────┘                 └───────────────────────────────────┬─────────────────────────────────┘
                                                                        │
                                                                        │
                                    ┌───────────────────────────────────▼─────────────────────────────────┐
                                    │                                                                     │
                                    │                       Is Time-Sensitive?                           │
                                    │                                                                     │
                                    └───────────┬───────────────────────────────────────┬─────────────────┘
                                                │                                       │
                                                │ No                                    │ Yes
                                                │                                       │
                                    ┌───────────▼───────────────┐           ┌───────────▼─────────────────┐
                                    │                           │           │                             │
                                    │      Check Cache          │           │     Skip Cache Check        │
                                    │      (db.py)              │           │                             │
                                    │                           │           │                             │
                                    └───────────┬───────────────┘           └─────────────┬───────────────┘
                                                │                                         │
                                                │                                         │
                                    ┌───────────▼───────────────┐                         │
                                    │                           │                         │
                                    │     Cache Hit?            │                         │
                                    │                           │                         │
                                    └───────────┬───────────────┘                         │
                                                │                                         │
                                                │ No                                      │
                                                │                                         │
                                    ┌───────────▼───────────────┐                         │
                                    │                           │                         │
                                    │    Web Search (DuckDuckGo)│◀────────────────────────┘
                                    │                           │
                                    └───────────┬───────────────┘
                                                │
                                                │
                                    ┌───────────▼───────────────┐
                                    │                           │
                                    │  Parallel URL Scraping    │
                                    │  (content_scraper.py)     │
                                    │                           │
                                    └───────────┬───────────────┘
                                                │
                                                │
                                    ┌───────────▼───────────────┐
                                    │                           │
                                    │  Focused Content Extraction│
                                    │  (focused_extractor.py)   │
                                    │                           │
                                    └───────────┬───────────────┘
                                                │
                                                │
                                    ┌───────────▼───────────────┐
                                    │                           │
                                    │  AI Summary Generation    │
                                    │  (summarizer.py)          │
                                    │                           │
                                    └───────────┬───────────────┘
                                                │
                                                │
                                    ┌───────────▼───────────────┐
                                    │                           │
                                    │  Cache Results            │
                                    │  (db.py)                  │
                                    │                           │
                                    └───────────┬───────────────┘
                                                │
                                                │
┌─────────────────┐                 ┌───────────▼───────────────┐
│                 │                 │                           │
│  Display Results│◀────────────────│  Return Response         │
│                 │                 │                           │
└─────────────────┘                 └───────────────────────────┘
```

## Data Flow

1. **User Input**: The user enters a query in the frontend's QueryInput component
2. **Query Submission**: The query is sent to the backend via a POST request to `/query/stream/{ws_id}`
3. **WebSocket Connection**: A WebSocket connection is established for real-time status updates
4. **Query Processing**: The backend processes the query through the pipeline:
   - Validates the query using the simplexity classifier
   - Checks the cache for similar queries (if not time-sensitive)
   - Searches the web for relevant content
   - Scrapes content from the search results
   - Extracts focused content from the scraped data
   - Generates a summary using the Groq LLM
   - Caches the results for future use
5. **Status Updates**: Throughout the process, status updates are sent to the frontend via WebSocket
6. **Result Display**: The frontend displays the results using the QueryResults component

## Key Technologies

### Backend
- **FastAPI**: Web framework for API endpoints and WebSockets
- **Groq**: LLM provider for classification, extraction, and summarization
- **Selenium**: Web scraping with browser automation
- **BeautifulSoup**: HTML parsing and content extraction
- **Chroma DB**: Vector database for query caching
- **DuckDuckGo Search**: Web search API

### Frontend
- **React**: UI library for component-based development
- **TypeScript**: Type-safe JavaScript
- **ReactMarkdown**: Markdown rendering for summaries
- **WebSockets**: Real-time communication with the backend

## Conclusion

The Ripplica Query Core system demonstrates a sophisticated approach to web search and summarization. By combining traditional web scraping techniques with modern LLM capabilities, it provides users with comprehensive answers to their queries based on the latest information available on the web. The modular architecture allows for easy maintenance and extension, while the caching mechanism improves performance for repeated or similar queries.