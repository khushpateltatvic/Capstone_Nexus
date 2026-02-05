
from typing import TypedDict, Optional, Dict, Any, List
import operator
import logging
import asyncio

try:
    from langgraph.graph import StateGraph, END
except ImportError:
    StateGraph = None

# Agents
from .agents.router import RouterAgent
from .agents.historian import HistorianAgent
from .agents.pm import PMAgent
from .agents.auditor import AuditorAgent
from .agents.tech_lead import TechLeadAgent
from .agents.strategist import StrategistAgent
from .agents.reducer import reducer

# Services
from app.services.rag.query_service import rag_service

# --- State Definition ---
class AgentState(TypedDict):
    # Inputs
    input_text: str  # Original Document Text (if applicable)
    metadata: Dict[str, Any] # Contains client_id, project_id, project_name
    
    # Retrieved Contexts (The "Brain" Memory)
    univ_context: Optional[str]
    ops_context: Optional[str]
    tech_context: Optional[str]
    commercial_context: Optional[str]
    strategy_context: Optional[str]
    marketing_context: Optional[str]
    
    # Agent Outputs
    historian_output: Optional[Dict[str, Any]]
    pm_output: Optional[Dict[str, Any]]
    auditor_output: Optional[Dict[str, Any]]
    tech_lead_output: Optional[Dict[str, Any]]
    strategist_output: Optional[Dict[str, Any]]
    
    final_output: Optional[Dict[str, Any]]

# --- Nodes ---

def normalize_state(state: Any) -> Dict[str, Any]:
    """Ensures state is a dictionary."""
    if isinstance(state, list):
        return state[-1] if state else {}
    return state or {}

async def retrieval_node(state: AgentState):
    """
    The Intelligence Gathering Phase.
    Fetches all relevant contexts from Vector Store in parallel.
    """
    state = normalize_state(state)
    meta = state.get("metadata", {})
    client_id = meta.get("client_id", "default")
    project_id = meta.get("project_id", "default")
    project_name = meta.get("project_name")
    
    logging.info(f"[{project_id}] Graph: Starting Retrieval Node...")

    # Parallel Retrieval
    # We fetch ALL contexts. The Router logic later decides if they are useful.
    # This ensures we don't miss anything that MIGHT be relevant.
    results = await asyncio.gather(
        rag_service.retrieve_context("universal_context", client_id, project_id, project_name),
        rag_service.retrieve_context("operations", client_id, project_id, project_name),
        rag_service.retrieve_context("technical", client_id, project_id, project_name),
        rag_service.retrieve_context("commercial", client_id, project_id, project_name),
        rag_service.retrieve_context("strategy", client_id, project_id, project_name),
        rag_service.retrieve_context("marketing", client_id, project_id, project_name)
    )
    
    return {
        "univ_context": results[0],
        "ops_context": results[1],
        "tech_context": results[2],
        "commercial_context": results[3],
        "strategy_context": results[4],
        "marketing_context": results[5]
    }

async def historian_node(state: AgentState):
    state = normalize_state(state)
    agent = HistorianAgent()
    meta = state.get("metadata", {})
    project_name = meta.get("project_name", "Unknown Project")
    
    # Historian needs document text + context
    ctx = state.get("univ_context", "")
    result = await agent.run(ctx, ctx, project_name=project_name) 
    return {"historian_output": result}

async def pm_node(state: AgentState):
    state = normalize_state(state)
    agent = PMAgent()
    meta = state.get("metadata", {})
    project_name = meta.get("project_name", "Unknown Project")
    
    ctx = state.get("ops_context", "")
    result = await agent.run(ctx, "[]", project_name=project_name)
    return {"pm_output": result}

async def auditor_node(state: AgentState):
    state = normalize_state(state)
    agent = AuditorAgent()
    meta = state.get("metadata", {})
    project_name = meta.get("project_name", "Unknown Project")
    
    ctx = state.get("commercial_context", "")
    result = await agent.run(ctx, project_name=project_name)
    return {"auditor_output": result}

async def tech_lead_node(state: AgentState):
    state = normalize_state(state)
    agent = TechLeadAgent()
    meta = state.get("metadata", {})
    project_name = meta.get("project_name", "Unknown Project")
    
    ctx = state.get("tech_context", "")
    result = await agent.run(ctx, project_name=project_name)
    return {"tech_lead_output": result}

async def strategist_node(state: AgentState):
    state = normalize_state(state)
    agent = StrategistAgent()
    meta = state.get("metadata", {})
    project_name = meta.get("project_name", "Unknown Project")
    
    # Combine Strategy + Marketing
    s_ctx = state.get("strategy_context", "")
    m_ctx = state.get("marketing_context", "")
    combined = f"{s_ctx}\n\n{m_ctx}"
    result = await agent.run(combined, project_name=project_name)
    return {"strategist_output": result}

async def reducer_node(state: AgentState):
    state = normalize_state(state)
    logging.info("Graph: Reducer aggregating usage...")
    # Call the production reducer which persists to Mongo
    result = await reducer.reduce_and_persist(state)
    return {"final_output": result}

# --- Router Logic (Edges) ---

def route_agents(state: AgentState):
    """
    The Smart Router.
    Decides which agents to run based on the QUALITY of retrieved context.
    Prevents Hallucinations by not running agents on empty data.
    """
    state = normalize_state(state)
    active_nodes = []
    
    # Rule 1: Always run Historian & PM (General Info)
    # But only if we actually found something
    if state.get("univ_context") or state.get("ops_context"):
        active_nodes.append("historian_node")
        active_nodes.append("pm_node")
        
    # Rule 2: Run Tech Lead ONLY if technical context exists
    tech = state.get("tech_context", "")
    if tech and len(tech.strip()) > 50: # Threshold to avoid noise
        active_nodes.append("tech_lead_node")
    else:
        logging.info("Graph Router: Skipping Tech Lead (No context found)")

    # Rule 3: Run Auditor ONLY if commercial context exists
    comm = state.get("commercial_context", "")
    if comm and len(comm.strip()) > 50:
        active_nodes.append("auditor_node")
    else:
        logging.info("Graph Router: Skipping Auditor (No context found)")
        
    # Rule 4: Run Strategist if strategy/marketing context exists
    strat = state.get("strategy_context", "") or state.get("marketing_context", "")
    if strat and len(strat.strip()) > 50:
        active_nodes.append("strategist_node")
    else:
        logging.info("Graph Router: Skipping Strategist (No context found)")

    # Fallback: If nothing was found, go straight to Reducer (or End)
    if not active_nodes:
        logging.warning("Graph Router: No relevant context found for ANY agent.")
        return ["reducer_node"]
        
    return active_nodes

# --- Graph Contruction ---
def build_graph():
    if not StateGraph:
        logging.error("LangGraph not installed!")
        return None
    
    workflow = StateGraph(AgentState)
    
    # 1. Add Nodes
    workflow.add_node("retrieval_node", retrieval_node)
    
    workflow.add_node("historian_node", historian_node)
    workflow.add_node("pm_node", pm_node)
    workflow.add_node("auditor_node", auditor_node)
    workflow.add_node("tech_lead_node", tech_lead_node)
    workflow.add_node("strategist_node", strategist_node)
    
    workflow.add_node("reducer_node", reducer_node)
    
    # 2. Set Entry
    workflow.set_entry_point("retrieval_node")
    
    # 3. Router Edge (Retrieval -> Agents)
    # The Router determines WHICH agents run based on the data found.
    workflow.add_conditional_edges(
        "retrieval_node",
        route_agents,
        [
            "historian_node", 
            "pm_node", 
            "auditor_node", 
            "tech_lead_node", 
            "strategist_node", 
            "reducer_node"
        ]
    )
    
    # 4. Fan-in (Agents -> Reducer)
    workflow.add_edge("historian_node", "reducer_node")
    workflow.add_edge("pm_node", "reducer_node")
    workflow.add_edge("auditor_node", "reducer_node")
    workflow.add_edge("tech_lead_node", "reducer_node")
    workflow.add_edge("strategist_node", "reducer_node")
    
    workflow.add_edge("reducer_node", END)
    
    return workflow.compile()
