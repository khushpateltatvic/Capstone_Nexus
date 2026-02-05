#!/usr/bin/env python3
"""
Test the processor and queue to see if documents are being processed
"""

import asyncio
import logging
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    try:
        logger.info("Testing processor and queue...")
        
        from app.core.memory_adapters import msg_queue
        from app.services.ingestion.processor import processor
        
        # Check queue status
        queue_size = msg_queue.qsize()
        logger.info(f"📊 Current queue size: {queue_size}")
        
        if queue_size > 0:
            logger.info("📄 Queue has items - checking what's in it...")
            
            # Peek at queue items (without removing them)
            items = []
            temp_items = []
            
            # Dequeue all items to see them, then re-queue
            while not msg_queue.empty():
                item = await msg_queue.dequeue()
                if item:
                    items.append(item)
                    temp_items.append(item)
            
            # Re-queue the items
            for item in temp_items:
                await msg_queue.enqueue(item)
            
            logger.info(f"📄 Found {len(items)} items in queue:")
            for i, item in enumerate(items):
                logger.info(f"   {i+1}. {item.get('filename', 'unknown')} - {item.get('client_id', 'unknown')}/{item.get('project_id', 'unknown')}")
                logger.info(f"      Content size: {len(item.get('content', b''))} bytes")
                logger.info(f"      Source: {item.get('source', 'unknown')}")
        else:
            logger.info("📄 Queue is empty")
        
        # Test processing one item manually
        if queue_size > 0:
            logger.info("🧪 Testing manual processing of one item...")
            item = await msg_queue.dequeue()
            if item:
                logger.info(f"📄 Processing: {item.get('filename', 'unknown')}")
                await processor._process_item(item)
                logger.info("✅ Manual processing completed")
        
        # Check queue size after processing
        final_queue_size = msg_queue.qsize()
        logger.info(f"📊 Final queue size: {final_queue_size}")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())