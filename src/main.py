import asyncio
import json
import logging
logging.basicConfig(format="%(asctime)s %(levelname)s %(name)s: lines %(lineno)d: %(message)s", filename="./tiken_bot.log", encoding="utf-8", level=logging.INFO)
from uuid import uuid4

from observer import observer


with open("./config.json") as f:
    config = json.loads(f.read())

TOKEN = config["TOKEN"]

# set logger
logger = logging.getLogger(__name__)

async def main():
    ws_url = f"wss://misskey.io/streaming?i={TOKEN}"

    channels = {
        str(uuid4()): "hybridTimeline",
        str(uuid4()): "main",
    }

    await observer(ws_url, channels)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(e)