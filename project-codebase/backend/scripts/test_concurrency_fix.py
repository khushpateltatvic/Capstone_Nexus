
import asyncio
import logging
import time
from unittest.mock import MagicMock, patch
from httpx import Response
from app.services.ingestion.basecamp import basecamp_service
from app.services.ingestion.watchdog import watchdog

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

async def heartbeat():
    """Simulate a concurrent task (like API handling) that shouldn't be blocked."""
    max_lag = 0
    for _ in range(10): # Run for 5 seconds (10 * 0.5s)
        start = time.time()
        await asyncio.sleep(0.5)
        lag = time.time() - start - 0.5
        max_lag = max(max_lag, lag)
        logging.info(f"❤️ Heartbeat (Lag: {lag:.4f}s)")
        if lag > 0.1:
            logging.error(f"⚠️ Event loop blocked! Lag: {lag:.4f}s")
    
    return max_lag

async def mock_basecamp_sync():
    """Run the Basecamp sync with mocked network calls."""
    logging.info("🚀 Starting Mock Sync...")
    
    # Mock httpx responses with delays to simulate network latency
    async def mock_handler(*args, **kwargs):
        await asyncio.sleep(0.5) # Simulate network delay
        return Response(200, json={"mock": "data", "id": 1})

    # We need to patch the internal _get methods or just run it if we can mock the client
    # But since we use httpx.AsyncClient inside sync_all_projects, we need to mock httpx.AsyncClient
    
    with patch("httpx.AsyncClient") as MockClient:
        # MockClient() returns the client instance
        # And we use it as a context manager: async with httpx.AsyncClient() as client
        # so we need to mock __aenter__
        
        mock_client_instance = MagicMock()
        mock_client_instance.get.side_effect = mock_handler
        
        mock_context_manager = MockClient.return_value
        mock_context_manager.__aenter__.return_value = mock_client_instance
        
        # Override project_ids to force execution
        basecamp_service.project_ids = ["123", "456"]
        
        await basecamp_service.sync_all_projects()
    
    logging.info("✅ Mock Sync Completed")

async def test_concurrency():
    logging.info("🧪 Starting Concurrency Test")
    
    # Run heartbeat and sync concurrently
    # Create tasks
    heartbeat_task = asyncio.create_task(heartbeat())
    sync_task = asyncio.create_task(mock_basecamp_sync())
    
    # Wait for both
    await asyncio.gather(heartbeat_task, sync_task)
    
    max_lag = await heartbeat_task
    
    logging.info(f"📊 Test Results: Max Heartbeat Lag = {max_lag:.4f}s")
    
    if max_lag < 0.2:
        logging.info("✅ SUCCESS: Event loop remained responsive!")
    else:
        logging.error("❌ FAILURE: Event loop was blocked significantly.")

if __name__ == "__main__":
    asyncio.run(test_concurrency())
