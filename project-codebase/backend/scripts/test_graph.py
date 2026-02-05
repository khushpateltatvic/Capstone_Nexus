
import asyncio
import logging
import sys
import os

# Add current dir to path
sys.path.append(os.getcwd())

from app.services.intelligence.graph import build_graph
from app.core.database import db

# Configure logging to see the graph working
logging.basicConfig(
    level=logging.ERROR, # Reduce noise
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_graph():
    print("--- LangGraph Test ---")
    
    # Initialize DB (Required for Reducer)
    await db.connect()
    
    workflow = build_graph()
    if not workflow:
        print("❌ LangGraph failed to compile (Is langgraph installed?)")
        return

    # Mock Input
    state = {
        "metadata": {
            "client_id": "test_client",
            "project_id": "test_project",
            "project_name": "ICICI Lombard GA4", # Real project name to find data
            "filename": "test_manual_trigger.txt"
        }
    }
    
    print(f"Invoking graph for project: {state['metadata']['project_name']}...")
    
    try:
        # Run graph
        result = await workflow.ainvoke(state)
        
        print("\n--- Execution Result ---")
        final = result.get("final_output", {})
        print(f"Fields Updated: {final.get('fields_updated')}")
        
        # Check specific agent outputs
        agents = ["historian", "pm", "tech_lead", "auditor", "strategist"]
        for agent in agents:
            output = result.get(f"{agent}_output")
            if output:
                print(f"✅ {agent.upper()} ran successfully. Keys: {list(output.keys())}")
            else:
                print(f"⚪ {agent.upper()} skipped (as expected by Router if no context found).")
                
    except Exception as e:
        print(f"❌ Graph Execution Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_graph())
