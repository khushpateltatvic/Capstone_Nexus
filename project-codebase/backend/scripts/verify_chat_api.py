import asyncio
import httpx
import sys

async def test_chat_api():
    base_url = "http://localhost:8000/api/v1"
    
    test_queries = [
        "What is Project Nexus?",
        "Who is on the team?",
        "Are there any blockers for the current projects?"
    ]
    
    print("🚀 Starting Nexus Chatbot API Verification...")
    
    async with httpx.AsyncClient() as client:
        for query in test_queries:
            print(f"\n💬 Query: {query}")
            try:
                # Updated to use new endpoint structure
                response = await client.post(
                    f"{base_url}/chat/ask",
                    json={"message": query, "history": []},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Response received:")
                    print(f"---")
                    print(data["answer"])
                    print(f"---")
                    print(f"📚 Sources: {', '.join(data['sources']) if data['sources'] else 'None'}")
                else:
                    print(f"❌ Error: {response.status_code}")
                    print(response.text)
                    
            except Exception as e:
                print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--run":
        asyncio.run(test_chat_api())
    else:
        print("Verification script created. Run with '--run' to execute (requires backend running).")
