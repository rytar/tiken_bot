import asyncio
from uuid import uuid4

from config import TOKEN
from worker import worker

async def main():
    ws_url = f"wss://misskey.io/streaming?i={TOKEN}"

    channels = {
        str(uuid4()): "hybridTimeline",
        str(uuid4()): "main",
    }

    await worker(ws_url, channels)

if __name__ == "__main__":
    asyncio.run(main())