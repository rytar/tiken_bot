import asyncio
import json
import logging
from uuid import uuid4

from worker import worker


with open("../config.json") as f:
    config = json.loads(f.read())

TOKEN = config["TOKEN"]

# set logger
logger = logging.getLogger(__name__)
logging.basicConfig(format="%(asctime)s %(levelname)s %(name)s: lines %(lineno)d: %(message)s", filename="./observer.log", encoding="utf-8", level=logging.INFO)

async def main():
    ws_url = f"wss://misskey.io/streaming?i={TOKEN}"

    channels = {
        str(uuid4()): "hybridTimeline",
        str(uuid4()): "main",
    }

    await worker(ws_url, channels)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(e)