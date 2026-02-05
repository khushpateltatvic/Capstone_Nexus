import asyncio
from typing import Any, Optional, Dict
from cachetools import TTLCache
import time

class MemoryQueue:
    """Asyncio.Queue wrapper to simulate Redis queue interface"""
    def __init__(self):
        self._queue = asyncio.Queue()

    async def enqueue(self, item: Any):
        await self._queue.put(item)

    async def dequeue(self) -> Any:
        return await self._queue.get()

    def qsize(self) -> int:
        return self._queue.qsize()

class MemoryCache:
    """TTLCache wrapper to simulate Redis get/set interface"""
    def __init__(self, maxsize: int = 1000, ttl: int = 300):
        self._cache = TTLCache(maxsize=maxsize, ttl=ttl)

    async def get(self, key: str) -> Optional[Any]:
        return self._cache.get(key)

    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        # cachetools handles TTL at init, specific TTL per key is harder 
        # so we just accept the default for now or overwrite if needed.
        # For a more robust implementation we'd wrap value with expiry.
        self._cache[key] = value
    
    async def delete(self, key: str):
        if key in self._cache:
            del self._cache[key]
            
    async def clear(self):
        self._cache.clear()

class MemoryLock:
    """Asyncio.Lock wrapper with key-based locking simulation"""
    def __init__(self):
        self._locks: Dict[str, asyncio.Lock] = {}
        self._global_lock = asyncio.Lock()

    async def acquire(self, key: str) -> bool:
        async with self._global_lock:
            if key not in self._locks:
                self._locks[key] = asyncio.Lock()
        
        # This is a simple blocking acquire. 
        # Redis SETNX is non-blocking usually, so we might need a mix.
        # For now, we assume we want to wait for the lock.
        await self._locks[key].acquire()
        return True

    async def release(self, key: str):
        if key in self._locks:
            self._locks[key].release()

# Global instances (Singleton pattern for the app)
msg_queue = MemoryQueue()
response_cache = MemoryCache(ttl=300) # 5 minutes default
processing_lock = MemoryLock()
