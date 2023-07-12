import asyncio
import json
import logging
import requests
import time
from websockets.client import connect, WebSocketClientProtocol
from websockets.exceptions import ConnectionClosed


# set logger
logger = logging.getLogger(__name__)

Msg = dict[str, str | dict[str, str | dict]]
"""
The form of messages from the stream as below:
```
{
    "type": "channel",
    "body": {
        "id": "xxxxx",
        "type": "something",
        "body": {
            "some": "thing",
        }
    }
}
```

The reference is [here](https://misskey-hub.net/docs/api/streaming).
"""

last_renote = time.time()

def fire_and_forget(func):
    def wrapper(*args, **kwargs):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_in_executor(None, func, *args, *kwargs)
    return wrapper

def should_renote(note: dict):
    res = requests.post("http://localhost:5001/", json=note)
    data = res.json()
    return data["result"]

@fire_and_forget
def send(url: str, event: str, note: dict | None = None):
    global last_renote

    if event == "mention":
        logger.info(f"mention: {note['id']}")
        res = requests.post(url, json={ "event": event, "note": note })
        status = res.text
        logger.info(f"mention {note['id']}: {status}")

    elif event == "note":
        if not note["renoteId"] is None and note["text"] is None:
            note = note["renote"]
        
        if should_renote(note):
            res = requests.post(url, json={ "event": event, "note": note })
            status = res.text
            logger.info(f"note {note['id']}: {status}")

            if status == "successfully renoted":
                last_renote = time.time()
    
    elif event == "rerenote":
        last_renote = time.time()
        res = requests.post(url, json={ "event": event })
        status = res.text
        logger.info(f"rerenote: {status}")


async def worker(ws_url: str, channels: dict[str, str]):
    """
        The worker function which connect to the websocket and read the stream.

        A string (`ws_url`) is necessary for connecting to the API server.

        A dict (`channels`) are the pairs of uuid and the channel name.

        If you want to get the available channel names, see [the Misskey API document](https://misskey-hub.net/docs/api/streaming/channel/).

        Args:
            ws_url: websocket url
            channels: the pairs of uuid and the channel name
        Return:
            None
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    url = "http://localhost:5000/"
    rerenote_interval = 60 * 60 * 3
    
    async for ws in connect(ws_url):
        try:
            await connect_channels(ws, channels)

            async for data in ws:
                msg: Msg = json.loads(data)

                if not msg["type"] == "channel": continue

                channel = channels[msg["body"]["id"]]
                event: str = msg["body"]["type"]

                if channel == "main" and event == "mention" or event == "note":
                    note: dict = msg["body"]["body"]

                    send(url, event, note)
                
                if time.time() - last_renote > rerenote_interval:
                    send(url, "rerenote")

        except ConnectionClosed as e:
            logger.error(e)
            continue

async def connect_channels(ws: WebSocketClientProtocol, channels: dict[str, str]):
    for uuid, channel in channels.items():
        logger.info(f"connect to {channel} with id: {uuid}")

        await ws.send(json.dumps({
            "type": "connect",
            "body": {
                "channel": channel,
                "id": uuid
            }
        }))


if __name__ == "__main__":
    import asyncio
    import json
    from uuid import uuid4

    config = json.load("../config.json")
    token = config["TOKEN"]
    ws_url = f"wss://misskey.io/streaming?i={token}"

    channels = {}
    channels[str(uuid4())] = "hybridTimeline"

    asyncio.run(worker(ws_url, channels))