# 🎯 Multi-Agent System Implementation Guide

## Understanding the Multi-Agent Architecture

This RAG system implements a **sophisticated multi-agent workflow** using LangGraph. Each agent has a specific role and works together to provide intelligent, context-aware responses.

## The Four Agents Explained

### 1. 🎯 Router Agent

**Role**: Query Intelligence & Routing

**Decision Process**:
```
Input: User Query
↓
Analysis:
- Does this require knowledge base search?
- Is this a general conversation?
- What's the intent?
↓
Output: Route Decision (RAG or Direct)
```

**Example**:
- Query: "What is the capital of France?" → **Direct** (general knowledge)
- Query: "What does our employee handbook say about vacation?" → **RAG** (needs documents)

**Implementation**:
```python
async def router_agent(self, state: GraphState) -> GraphState:
    system_prompt = """Analyze the query and determine:
    1. Does it require searching a knowledge base?
    2. Or can it be answered directly?
    Respond with JSON: {"route": "query" or "direct"}
    """
    decision = await self.llm.ainvoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=query)
    ])
    return updated_state
```

### 2. 🔍 Query Agent

**Role**: Document Retrieval & Context Gathering

**Process**:
```
Input: Query + Route Decision
↓
1. Generate Query Embedding
   query_vector = embedding_model.embed(query)
↓
2. Search Vector Database
   results = qdrant.search(
       vector=query_vector,
       top_k=5,
       score_threshold=0.7
   )
↓
3. Retrieve Top Documents
   chunks = [result.content for result in results]
↓
Output: Ranked Document Chunks + Relevance Scores
```

**Key Features**:
- Semantic search using embeddings
- Score-based filtering
- Metadata-aware retrieval
- Configurable top-k

**Code**:
```python
async def query_agent(self, state: GraphState) -> GraphState:
    query = state["query"]
    
    # Generate embedding and search
    search_results = await self.vector_search_func(query)
    
    state["search_results"] = [
        {
            "content": r.content,
            "score": r.score,
            "metadata": r.metadata,
        }
        for r in search_results
    ]
    
    return state
```

### 3. 📊 Evaluation Agent

**Role**: Quality Assessment & Refinement Decision

**Evaluation Criteria**:
```
Input: Query + Retrieved Documents
↓
Analysis:
1. Relevance Assessment
   - Are scores above threshold?
   - Does content match query intent?

2. Coverage Check
   - Is the query fully addressable?
   - Are there gaps?

3. Quality Metrics
   - Document diversity
   - Information completeness
↓
Decision: Sufficient → Proceed | Insufficient → Refine
```

**Refinement Loop**:
```
Iteration 1: Initial retrieval
↓
Evaluation: Insufficient
↓
Iteration 2: Refined retrieval (adjusted query)
↓
Evaluation: Sufficient
↓
Proceed to Response
```

**Implementation**:
```python
async def evaluation_agent(self, state: GraphState) -> GraphState:
    search_results = state.get("search_results", [])
    
    system_prompt = """Assess if search results are sufficient:
    1. Check relevance scores
    2. Verify content quality
    3. Ensure query coverage
    
    Respond: {"sufficient": true/false, "reasoning": "..."}
    """
    
    assessment = await self.llm.ainvoke([...])
    state["metadata"]["evaluation"] = assessment.content
    
    return state
```

**Decision Logic**:
```python
def _evaluation_decision(self, state: GraphState) -> str:
    # Check max iterations
    if state["iteration"] >= self.max_iterations:
        return "respond"
    
    # Parse evaluation
    evaluation = state["metadata"].get("evaluation", "")
    if "sufficient" in evaluation and "true" in evaluation:
        return "respond"
    
    return "refine"  # Another iteration
```

### 4. 💬 Response Agent

**Role**: Answer Generation & Citation

**Process**:
```
Input: Query + Validated Context Documents
↓
1. Context Building
   context = format_sources(documents)
↓
2. Prompt Engineering
   prompt = f"""
   Context: {context}
   Query: {query}
   
   Instructions:
   - Use only provided context
   - Cite sources
   - Be precise
   """
↓
3. LLM Generation
   answer = llm.invoke(prompt)
↓
4. Post-processing
   - Add citations
   - Format response
   - Include metadata
↓
Output: Final Answer + Sources
```

**Implementation**:
```python
async def response_agent(self, state: GraphState) -> GraphState:
    query = state["query"]
    results = state.get("search_results", [])
    
    # Build context from sources
    context = "\n\n".join([
        f"[Source {i+1}] (Score: {r['score']})\n{r['content']}"
        for i, r in enumerate(results[:5])
    ])
    
    system_prompt = """You are a helpful AI assistant.
    Use the provided context to answer the query.
    Be precise and cite sources when possible.
    If the context doesn't contain relevant information, say so.
    """
    
    response = await self.llm.ainvoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Context:\n{context}\n\nQuery: {query}")
    ])
    
    state["answer"] = response.content
    return state
```

## LangGraph Workflow

### Graph Structure

```python
workflow = StateGraph(GraphState)

# Add agents as nodes
workflow.add_node("router_agent", self.router_agent)
workflow.add_node("query_agent", self.query_agent)
workflow.add_node("evaluation_agent", self.evaluation_agent)
workflow.add_node("response_agent", self.response_agent)

# Define edges
workflow.set_entry_point("router_agent")

# Conditional routing from router
workflow.add_conditional_edges(
    "router_agent",
    self._route_decision,
    {
        "query": "query_agent",      # Needs RAG
        "direct": "response_agent",   # Direct answer
    }
)

# Query → Evaluation
workflow.add_edge("query_agent", "evaluation_agent")

# Conditional routing from evaluation
workflow.add_conditional_edges(
    "evaluation_agent",
    self._evaluation_decision,
    {
        "refine": "query_agent",      # Loop back
        "respond": "response_agent",  # Proceed
    }
)

# Response → End
workflow.add_edge("response_agent", END)

# Compile
graph = workflow.compile()
```

### State Management

```python
class GraphState(TypedDict):
    messages: List[BaseMessage]      # Conversation history
    query: str                       # User query
    search_results: List[Dict]       # Retrieved documents
    answer: str                      # Final answer
    current_agent: str               # Current agent name
    metadata: Dict[str, Any]         # Agent metadata
    iteration: int                   # Current iteration
```

## Workflow Examples

### Example 1: Simple Query (Direct Path)

```
Query: "What is 2+2?"
→ Router Agent: "This is general math, no RAG needed"
→ Response Agent: "2+2 equals 4"
→ Done (1 agent hop)
```

### Example 2: Knowledge Base Query (Full Path)

```
Query: "What is our company's remote work policy?"

→ Router Agent: 
   Analysis: "Needs company documents"
   Decision: Route to RAG

→ Query Agent:
   Embedding: [0.234, 0.567, ...]
   Search Results: [
       {content: "Remote work is allowed...", score: 0.92},
       {content: "Employees can work remotely...", score: 0.87}
   ]

→ Evaluation Agent:
   Assessment: "High scores (0.92, 0.87), good coverage"
   Decision: Sufficient

→ Response Agent:
   Context: "[Source 1] Remote work is allowed..."
   Answer: "According to our policy [Source 1], remote work..."
   
→ Done (4 agent hops)
```

### Example 3: Iterative Refinement

```
Query: "Tell me about project deadlines"

Iteration 1:
→ Query Agent: Searches for "project deadlines"
   Results: [score: 0.65, 0.62] (below ideal threshold)

→ Evaluation Agent: "Scores low, coverage incomplete"
   Decision: Refine

Iteration 2:
→ Query Agent: Refined search "project timeline deliverables"
   Results: [score: 0.89, 0.85, 0.82]

→ Evaluation Agent: "Much better, sufficient"
   Decision: Proceed

→ Response Agent: Generates comprehensive answer

→ Done (6 agent hops, 2 iterations)
```

## Configuration

### Agent Parameters

```python
# In .env or config
AGENT_MAX_ITERATIONS=10      # Max refinement loops
AGENT_TIMEOUT=300            # Timeout in seconds
RAG_TOP_K=5                  # Documents to retrieve
RAG_SCORE_THRESHOLD=0.7      # Minimum relevance score
```

### Customizing Agents

```python
# Custom prompts
ROUTER_PROMPT = "Custom routing logic..."
EVALUATION_PROMPT = "Custom evaluation criteria..."

# Custom decision logic
def custom_route_decision(state: GraphState) -> str:
    # Your custom logic
    return "query" or "direct"
```

## Benefits of Multi-Agent Approach

1. **Modularity**: Each agent has a single responsibility
2. **Flexibility**: Easy to modify individual agents
3. **Observability**: Track each agent's decisions
4. **Quality**: Iterative refinement improves results
5. **Scalability**: Add new agents without breaking existing ones

## Monitoring & Debugging

### Logging Agent Decisions

```python
logger.info(f"Router Agent decided: {decision}")
logger.info(f"Query Agent retrieved: {len(results)} documents")
logger.info(f"Evaluation Agent: {assessment}")
logger.info(f"Response Agent generated answer in {time}ms")
```

### Tracking State

```python
# Access full execution trace
final_state = await graph.ainvoke(initial_state)

print(f"Total iterations: {final_state['iteration']}")
print(f"Agents called: {final_state['metadata']['agent_trace']}")
print(f"Documents used: {len(final_state['search_results'])}")
```

## Advanced Patterns

### Adding More Agents

```python
# Add a summarization agent
workflow.add_node("summarizer_agent", self.summarizer_agent)
workflow.add_edge("response_agent", "summarizer_agent")

# Add a fact-checking agent
workflow.add_node("fact_checker", self.fact_checker_agent)
workflow.add_edge("response_agent", "fact_checker")
```

### Parallel Agent Execution

```python
# Run multiple retrieval strategies in parallel
workflow.add_node("dense_retrieval", self.dense_agent)
workflow.add_node("sparse_retrieval", self.sparse_agent)

# Merge results
workflow.add_node("merger", self.merge_agent)
```

## Summary

The multi-agent system provides:
- **Intelligent Routing**: Don't waste resources on simple queries
- **Quality Retrieval**: Find the most relevant documents
- **Iterative Improvement**: Refine until satisfied
- **Reliable Answers**: Generate accurate, cited responses

This architecture scales from simple FAQ bots to complex enterprise knowledge systems! 🚀
