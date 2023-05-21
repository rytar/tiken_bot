import asyncio
from uuid import uuid4

from config import TOKEN
from worker import worker

async def main():
    num_workers = 1
    
    ws_url = f"wss://misskey.io/streaming?i={TOKEN}"

    channels = {
        str(uuid4()): "hybridTimeline",
        str(uuid4()): "main",
    }

    await asyncio.gather(
        *[ worker(ws_url, channels) for _ in range(num_workers) ]
    )

if __name__ == "__main__":
    asyncio.run(main())