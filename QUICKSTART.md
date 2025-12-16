# 🚀 Enterprise RAG System - Quick Start Guide

## Installation Steps

### 1. Install Dependencies
```bash
# Ensure you have uv installed
# If not: curl -LsSf https://astral.sh/uv/install.sh | sh

# Install project dependencies
uv pip install -e .
```

### 2. Set Up Environment
```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your API keys:
# - OPENAI_API_KEY (required if using OpenAI)
# - Or configure Ollama for local LLM
```

### 3. Start Infrastructure
```bash
# Start Qdrant, Ollama, PostgreSQL, Redis
docker-compose up -d

# Wait for services to be healthy
docker-compose ps
```

### 4. (Optional) Pull Ollama Model
```bash
# If using local LLM
docker exec -it rag_ollama ollama pull llama2
```

### 5. Run the Application
```bash
# Development mode with auto-reload
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Or
python -m src.main
```

### 6. Test the API
```bash
# Visit the API docs
open http://localhost:8000/docs

# Or test with curl
curl http://localhost:8000/health
```

## Multi-Agent System Explanation

The system uses **4 specialized agents**:

1. **Router Agent**: Analyzes incoming queries and routes them appropriately
2. **Query Agent**: Retrieves relevant documents from the vector database
3. **Evaluation Agent**: Assesses the quality and sufficiency of retrieved results
4. **Response Agent**: Generates the final answer using LLM

### Workflow:
```
User Query → Router → Query → Evaluation → Response → Final Answer
                │                  │
                └─── Direct ───────┘
                   (simple queries)
```

## Next Steps

1. Upload a document: `POST /api/v1/documents/upload`
2. Index it: `POST /api/v1/documents/index`
3. Query it: `POST /api/v1/rag/query`

Enjoy! 🎉
