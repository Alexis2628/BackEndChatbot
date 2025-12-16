# 🏗️ Architecture Documentation

## System Overview

The Enterprise RAG System is built following **Domain-Driven Design (DDD)** principles and the **Repository Pattern**, ensuring clean separation of concerns and high maintainability.

## Multi-Agent Architecture

### Agent Types

#### 1. Router Agent
- **Purpose**: Query analysis and routing
- **Input**: User query
- **Output**: Routing decision (RAG vs. Direct)
- **Logic**: Uses LLM to determine if query requires document retrieval

#### 2. Query Agent
- **Purpose**: Document retrieval
- **Input**: Query + routing decision
- **Output**: Relevant document chunks with scores
- **Logic**: 
  - Generates query embedding
  - Searches Qdrant vector DB
  - Retrieves top-k results

#### 3. Evaluation Agent
- **Purpose**: Result quality assessment
- **Input**: Query + retrieved results
- **Output**: Sufficiency decision
- **Logic**:
  - Evaluates relevance scores
  - Checks content coverage
  - Decides if refinement needed

#### 4. Response Agent
- **Purpose**: Answer generation
- **Input**: Query + context documents
- **Output**: Final answer with citations
- **Logic**:
  - Builds context from documents
  - Generates answer using LLM
  - Adds source citations

### Agent Flow Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                        User Query                            │
└─────────────────────────┬────────────────────────────────────┘
                          │
                          ▼
                ┌──────────────────┐
                │  Router Agent    │
                │  (LLM Decision)  │
                └────────┬─────────┘
                         │
            ┌────────────┴────────────┐
            │                         │
            ▼                         ▼
     ┌──────────┐              ┌──────────────┐
     │  Direct  │              │  Query Agent │
     │ Response │              │  (Retrieve)  │
     └────┬─────┘              └──────┬───────┘
          │                           │
          │                           ▼
          │                  ┌─────────────────┐
          │                  │ Evaluation Agent│
          │                  │  (Assess Quality)│
          │                  └────────┬─────────┘
          │                           │
          │                  ┌────────┴────────┐
          │                  │                 │
          │              Sufficient?       Insufficient
          │                  │                 │
          │                  ▼                 ▼
          │            ┌──────────┐      ┌─────────┐
          │            │ Response │      │ Refine  │
          │            │  Agent   │      │ (Loop)  │
          │            └────┬─────┘      └────┬────┘
          │                 │                 │
          └─────────────────┴─────────────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │ Final Answer  │
                    └───────────────┘
```

## Layered Architecture

### Layer 1: API Layer (Controllers)
**Location**: `src/api/controllers/`

**Responsibilities**:
- Handle HTTP requests/responses
- Input validation
- DTO transformation
- Route requests to services

**Key Files**:
- `rag_controller.py`: Query endpoints
- `indexing_controller.py`: Document management endpoints

### Layer 2: Service Layer (Business Logic)
**Location**: `src/services/`

**Responsibilities**:
- Implement business rules
- Orchestrate repositories
- Coordinate multi-agent workflows
- Handle transactions

**Key Files**:
- `rag_service.py`: Query processing, agent orchestration
- `indexing_service.py`: Document processing, embedding generation

### Layer 3: Repository Layer (Data Access)
**Location**: `src/repositories/`

**Responsibilities**:
- Abstract data access
- Implement CRUD operations
- Handle database specifics

**Key Files**:
- `interfaces.py`: Repository contracts (ABCs)
- `qdrant_repository.py`: Vector DB implementation
- `mock_repositories.py`: In-memory implementations

### Layer 4: Domain Layer (Entities)
**Location**: `src/domain/`

**Responsibilities**:
- Define business entities
- Define domain logic
- No external dependencies

**Key Files**:
- `models.py`: Document, Chunk, Query, AgentState, etc.

## Data Flow

### Document Indexing Flow

```
1. User uploads document (PDF, DOCX, etc.)
   ↓
2. IndexingController receives file
   ↓
3. IndexingService:
   - Saves file to storage
   - Creates Document record
   ↓
4. Docling parses document
   ↓
5. Text splitter creates chunks
   ↓
6. Embedding model generates vectors
   ↓
7. QdrantRepository stores chunks with embeddings
   ↓
8. Document status → COMPLETED
```

### Query Processing Flow (with Agents)

```
1. User submits query
   ↓
2. RAGController receives request
   ↓
3. RAGService initiates workflow
   ↓
4. Multi-Agent System executes:
   a. Router Agent analyzes query
   b. Query Agent retrieves documents
   c. Evaluation Agent assesses quality
   d. Response Agent generates answer
   ↓
5. RAGService returns QueryResponse
   ↓
6. User receives answer + sources
```

## Technology Stack Integration

### Vector Database (Qdrant)
- **Purpose**: Store and search document embeddings
- **Connection**: Via QdrantRepository
- **Collections**: Document chunks with metadata

### LLM Integration
- **Providers**: OpenAI, Ollama
- **Usage**:
  - Agent decision-making
  - Answer generation
  - Query understanding

### Embeddings
- **Purpose**: Convert text to vectors
- **Models**: OpenAI text-embedding-3-small
- **Usage**: Query + document embeddings

### Document Processing (Docling)
- **Purpose**: Parse complex documents
- **Features**:
  - Layout analysis
  - Table extraction
  - Multi-format support

## Dependency Injection

**File**: `src/dependencies.py`

**Pattern**: Singleton + Factory

```python
# Service creation hierarchy
get_rag_service() → requires:
  ├── get_qdrant_repository()
  ├── get_query_repository()
  ├── get_embedding_model()
  └── get_llm()
```

## Configuration Management

**File**: `src/config.py`

**Pattern**: Pydantic Settings

- Environment variable based
- Type-safe validation
- Default values
- .env file support

## MCP (Model Context Protocol)

**Location**: `src/mcp/`

**Purpose**: Standardize context passing between components

**Key Features**:
- Token-aware context building
- Document prioritization
- Metadata management

## Scalability Considerations

### Horizontal Scaling
- Stateless API servers
- Shared Qdrant cluster
- Distributed caching (Redis)

### Performance Optimizations
- Async/await throughout
- Connection pooling
- Background job processing
- Caching strategies

### Production Enhancements
1. Replace mock repositories with SQLAlchemy
2. Add Celery for background tasks
3. Implement Redis caching
4. Add monitoring (Prometheus)
5. Add distributed tracing (Jaeger)

## Security

### Current Implementation
- Environment-based secrets
- CORS configuration
- Input validation

### Production Additions Needed
- JWT authentication
- Rate limiting
- API key management
- Encryption at rest
- Audit logging

## Testing Strategy

### Unit Tests
- Service layer logic
- Repository implementations
- Agent decision logic

### Integration Tests
- API endpoints
- Database operations
- LLM integrations

### E2E Tests
- Full query workflow
- Document indexing pipeline

## Monitoring & Observability

### Logging
- Structured logging (structlog)
- JSON format for production
- Log levels per component

### Metrics (Future)
- Query latency
- Document indexing speed
- Cache hit rates
- Agent decision accuracy

---

**Note**: This architecture is designed to be production-ready but may require additional hardening depending on specific deployment requirements.
