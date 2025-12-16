# Enterprise RAG System with Multi-Agent Architecture

A production-ready, modular Python implementation of a **Retrieval-Augmented Generation (RAG)** system with **LangGraph multi-agent workflows**, following strict **Domain-Driven Design (DDD)** and **Repository Pattern** principles.

## 🎯 Key Features

- **🤖 Multi-Agent System**: Stateful workflows using LangGraph with specialized agents:
  - **Router Agent**: Intelligent query routing
  - **Query Agent**: Document retrieval and search
  - **Evaluation Agent**: Result quality assessment
  - **Response Agent**: Final answer generation

- **📄 Advanced Document Processing**: IBM Docling for layout-aware parsing
- **🔍 Vector Search**: Qdrant for efficient semantic search
- **🧠 Flexible LLM Support**: OpenAI, Ollama, or vLLM
- **📊 MCP Protocol**: Model Context Protocol for standardized context access
- **🏗️ Clean Architecture**: Strict layered design with Repository Pattern

## 📁 Project Structure

```
BackEndChatbot/
├── src/
│   ├── domain/              # Domain models (business entities)
│   │   ├── models.py        # Document, Chunk, Query, AgentState, etc.
│   │   └── __init__.py
│   ├── api/                 # API layer (Controllers & DTOs)
│   │   ├── controllers/     # FastAPI route handlers
│   │   │   ├── rag_controller.py
│   │   │   ├── indexing_controller.py
│   │   │   └── __init__.py
│   │   ├── dtos.py          # Data Transfer Objects
│   │   └── __init__.py
│   ├── services/            # Business logic layer
│   │   ├── rag_service.py   # RAG query processing
│   │   ├── indexing_service.py  # Document indexing
│   │   └── __init__.py
│   ├── repositories/        # Data access layer
│   │   ├── interfaces.py    # Repository contracts
│   │   ├── qdrant_repository.py  # Vector DB implementation
│   │   ├── mock_repositories.py  # Development mocks
│   │   └── __init__.py
│   ├── agents/              # LangGraph multi-agent system
│   │   ├── multi_agent_system.py
│   │   └── __init__.py
│   ├── config.py            # Pydantic settings
│   ├── dependencies.py      # Dependency injection
│   └── main.py              # FastAPI application
├── tests/                   # Test suite
├── data/                    # Data storage
│   ├── uploads/             # Uploaded documents
│   └── logs/                # Application logs
├── docker-compose.yaml      # Docker services
├── Dockerfile               # Application container
├── pyproject.toml           # Project dependencies
├── .env.example             # Environment template
└── README.md
```

## 🏛️ Architecture

### Layered Architecture (Repository Pattern)

```
┌─────────────────────────────────────────┐
│         API Layer (Controllers)         │  ← HTTP Request/Response
├─────────────────────────────────────────┤
│       Service Layer (Business Logic)    │  ← RAGService, IndexingService
├─────────────────────────────────────────┤
│    Repository Layer (Data Access)       │  ← Qdrant, PostgreSQL, etc.
├─────────────────────────────────────────┤
│          Domain Layer (Models)          │  ← Entities, Value Objects
└─────────────────────────────────────────┘
```

### Multi-Agent Workflow

```
User Query → Router Agent → Query Agent → Evaluation Agent → Response Agent → Answer
                    │                            │
                    └──────── Direct ────────────┘
                                │
                         (if sufficient results)
```

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.11+
- Docker & Docker Compose
- uv (Astral's package manager)

### 2. Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd BackEndChatbot

# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv venv
uv pip install -e .

# For development dependencies
uv pip install -e ".[dev]"
```

### 3. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
# Required: OPENAI_API_KEY (or configure Ollama)
```

### 4. Start Infrastructure with Docker

```bash
# Start all services (Qdrant, Ollama, PostgreSQL, Redis)
docker-compose up -d

# Pull Ollama model (if using local LLM)
docker exec -it rag_ollama ollama pull llama2
```

### 5. Run the Application

```bash
# Development mode
uv run uvicorn src.main:app --reload

# Or using Python directly
python -m src.main
```

The API will be available at `http://localhost:8000`

## 📚 API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

#### Document Management
- `POST /api/v1/documents/upload` - Upload a document
- `POST /api/v1/documents/index` - Index documents
- `GET /api/v1/documents/{id}` - Get document details
- `GET /api/v1/documents/` - List all documents
- `DELETE /api/v1/documents/{id}` - Delete document

#### RAG Queries
- `POST /api/v1/rag/query` - Execute RAG query
- `GET /api/v1/rag/query/{id}` - Get query by ID
- `GET /api/v1/rag/queries/recent` - Recent queries

#### Health
- `GET /health` - Health check

### Example Usage

```bash
# Upload a document
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -F "file=@document.pdf"

# Index the document
curl -X POST "http://localhost:8000/api/v1/documents/index" \
  -H "Content-Type: application/json" \
  -d '{"document_ids": ["<document-id>"]}'

# Query the RAG system
curl -X POST "http://localhost:8000/api/v1/rag/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the main topic of the document?",
    "top_k": 5,
    "use_agent": true
  }'
```

## 🛠️ Technology Stack

| Component | Technology |
|-----------|-----------|
| **Framework** | FastAPI |
| **Orchestration** | LangGraph |
| **Document Processing** | Docling (IBM) |
| **Vector DB** | Qdrant |
| **LLM** | OpenAI / Ollama / vLLM |
| **Embeddings** | OpenAI / Custom |
| **Configuration** | Pydantic Settings |
| **Container** | Docker + Docker Compose |

## 🧪 Development

### Running Tests

```bash
# Run all tests
uv run pytest

# With coverage
uv run pytest --cov=src --cov-report=html
```

### Code Quality

```bash
# Format code
uv run black src/

# Lint
uv run ruff check src/

# Type checking
uv run mypy src/
```

## 📦 Deployment

### Using Docker

```bash
# Build the image
docker build -t rag-system:latest .

# Run with docker-compose
docker-compose up -d
```

### Environment Variables

See `.env.example` for all configuration options.

## 🤝 Contributing

1. Follow PEP 8 style guidelines
2. Add type hints to all functions
3. Write tests for new features
4. Update documentation

## 📄 License

[Your License Here]

## 🔗 Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Docling Documentation](https://github.com/DS4SD/docling)
- [Qdrant Documentation](https://qdrant.tech/documentation/)

## 📞 Support

For issues and questions, please create an issue in the repository.