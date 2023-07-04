import asyncio
import json
import logging
import requests
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

def should_renote(note: dict):
    res = requests.post("http://localhost:5001", json=note)
    data = res.json()
    return data["result"]

def send(url: str, event: str, note: dict):
    if event == "mention":
        logger.info(f"mention: {note['id']}")
        requests.post(url, json={ "type": event, "note": note })

    elif event == "note":
        if not note["renoteId"] is None and note["text"] is None:
            note = note["renote"]
        
        if should_renote(note):
            logger.info(f"tiken: {note['id']}")
            requests.post(url, json={ "type": event, "note": note })


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

                    loop.run_in_executor(None, send, "http://localhost:5000", event, note)

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