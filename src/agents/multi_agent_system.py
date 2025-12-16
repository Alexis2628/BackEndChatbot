"""
LangGraph Multi-Agent System for RAG.
Implements a stateful workflow with specialized agents.
"""

import logging
from typing import Any, Dict, List, TypedDict

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph

from src.domain.models import AgentState, AgentType, SearchResult

logger = logging.getLogger(__name__)


class GraphState(TypedDict):
    """State structure for LangGraph."""
    messages: List[BaseMessage]
    query: str
    search_results: List[Dict[str, Any]]
    answer: str
    current_agent: str
    metadata: Dict[str, Any]
    iteration: int


class MultiAgentRAGSystem:
    """Multi-agent RAG system using LangGraph."""

    def __init__(
        self,
        llm: ChatOpenAI,
        vector_search_func: Any,
        max_iterations: int = 10,
    ):
        """Initialize the multi-agent system."""
        self.llm = llm
        self.vector_search_func = vector_search_func
        self.max_iterations = max_iterations
        self.graph = self._build_graph()
        logger.info("Initialized MultiAgentRAGSystem")

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        workflow = StateGraph(GraphState)

        # Add nodes (agents)
        workflow.add_node("router_agent", self.router_agent)
        workflow.add_node("query_agent", self.query_agent)
        workflow.add_node("evaluation_agent", self.evaluation_agent)
        workflow.add_node("response_agent", self.response_agent)

        # Define edges (workflow)
        workflow.set_entry_point("router_agent")
        
        # Router decides the path
        workflow.add_conditional_edges(
            "router_agent",
            self._route_decision,
            {
                "query": "query_agent",
                "direct": "response_agent",
            }
        )
        
        # Query agent → Evaluation
        workflow.add_edge("query_agent", "evaluation_agent")
        
        # Evaluation decides if we need to refine or respond
        workflow.add_conditional_edges(
            "evaluation_agent",
            self._evaluation_decision,
            {
                "refine": "query_agent",
                "respond": "response_agent",
            }
        )
        
        # Response agent → END
        workflow.add_edge("response_agent", END)

        return workflow.compile()

    async def router_agent(self, state: GraphState) -> GraphState:
        """Router agent - decides query routing."""
        logger.info("Router Agent: Analyzing query")
        
        query = state["query"]
        
        # Use LLM to determine if this needs RAG or can be answered directly
        system_prompt = """You are a routing agent. Analyze the user's query and determine:
        1. Does it require searching a knowledge base (RAG)?
        2. Or can it be answered directly (general knowledge)?
        
        Respond with JSON: {"route": "query" or "direct", "reasoning": "..."}
        """
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Query: {query}"),
        ]
        
        response = await self.llm.ainvoke(messages)
        
        state["messages"].append(response)
        state["current_agent"] = AgentType.ROUTER.value
        state["metadata"]["router_decision"] = response.content
        
        logger.info(f"Router decision: {response.content}")
        return state

    async def query_agent(self, state: GraphState) -> GraphState:
        """Query agent - retrieves relevant documents."""
        logger.info("Query Agent: Retrieving documents")
        
        query = state["query"]
        iteration = state.get("iteration", 0)
        
        # Generate query embedding and search
        # This would use the vector_search_func injected
        search_results = await self.vector_search_func(query)
        
        state["search_results"] = [
            {
                "content": r.content,
                "score": r.score,
                "metadata": r.metadata,
            }
            for r in search_results
        ]
        state["iteration"] = iteration + 1
        state["current_agent"] = AgentType.QUERY.value
        
        logger.info(f"Query Agent: Retrieved {len(search_results)} results")
        return state

    async def evaluation_agent(self, state: GraphState) -> GraphState:
        """Evaluation agent - assesses result quality."""
        logger.info("Evaluation Agent: Assessing results")
        
        search_results = state.get("search_results", [])
        iteration = state["iteration"]
        
        # Evaluate if results are sufficient
        system_prompt = """You are an evaluation agent. Assess if the search results 
        are sufficient to answer the user's query. Consider:
        1. Relevance scores
        2. Content quality
        3. Coverage of the query
        
        Respond with JSON: {"sufficient": true/false, "reasoning": "..."}
        """
        
        results_summary = "\n".join([
            f"Result {i+1} (score: {r['score']}): {r['content'][:200]}..."
            for i, r in enumerate(search_results[:3])
        ])
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Query: {state['query']}\n\nResults:\n{results_summary}"),
        ]
        
        response = await self.llm.ainvoke(messages)
        
        state["messages"].append(response)
        state["current_agent"] = AgentType.EVALUATION.value
        state["metadata"]["evaluation"] = response.content
        
        logger.info(f"Evaluation: {response.content}")
        return state

    async def response_agent(self, state: GraphState) -> GraphState:
        """Response agent - generates final answer."""
        logger.info("Response Agent: Generating final answer")
        
        query = state["query"]
        search_results = state.get("search_results", [])
        
        # Build context from search results
        context = "\n\n".join([
            f"[Source {i+1}] (Score: {r['score']})\n{r['content']}"
            for i, r in enumerate(search_results[:5])
        ])
        
        system_prompt = """You are a helpful AI assistant. Use the provided context 
        to answer the user's query. Be precise and cite sources when possible.
        If the context doesn't contain relevant information, say so.
        """
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Context:\n{context}\n\nQuery: {query}"),
        ]
        
        response = await self.llm.ainvoke(messages)
        
        state["answer"] = response.content
        state["messages"].append(response)
        state["current_agent"] = "response"
        
        logger.info("Response Agent: Generated final answer")
        return state

    def _route_decision(self, state: GraphState) -> str:
        """Decide routing based on router agent output."""
        # Parse router decision (simplified - in production, use proper JSON parsing)
        decision = state["metadata"].get("router_decision", "")
        if "direct" in decision.lower():
            return "direct"
        return "query"

    def _evaluation_decision(self, state: GraphState) -> str:
        """Decide if we need to refine or respond."""
        iteration = state["iteration"]
        
        # Max iterations check
        if iteration >= self.max_iterations:
            logger.warning(f"Max iterations ({self.max_iterations}) reached")
            return "respond"
        
        # Parse evaluation (simplified)
        evaluation = state["metadata"].get("evaluation", "")
        if "sufficient" in evaluation.lower() and "true" in evaluation.lower():
            return "respond"
        
        return "refine"

    async def execute(self, query: str) -> Dict[str, Any]:
        """Execute the multi-agent workflow."""
        logger.info(f"Executing multi-agent workflow for query: {query}")
        
        initial_state: GraphState = {
            "messages": [],
            "query": query,
            "search_results": [],
            "answer": "",
            "current_agent": "",
            "metadata": {},
            "iteration": 0,
        }
        
        final_state = await self.graph.ainvoke(initial_state)
        
        return {
            "answer": final_state["answer"],
            "sources": final_state["search_results"],
            "metadata": final_state["metadata"],
            "iterations": final_state["iteration"],
        }
