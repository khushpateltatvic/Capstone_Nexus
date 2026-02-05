import asyncio
from app.core.memory_adapters import msg_queue

async def main():
    print(f"Queue type: {type(msg_queue)}")
    if hasattr(msg_queue, 'qsize'):
        print(f"Queue size: {msg_queue.qsize()}")
    else:
        print("Queue does not support qsize()")

if __name__ == "__main__":
    asyncio.run(main())
