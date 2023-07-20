import asyncio
import json
import logging
import numpy as np
import time
from websockets.client import connect, WebSocketClientProtocol
from websockets.exceptions import ConnectionClosed

from execute import init, renote, rerenote, process_query
from fastText import FastTextModel
from utils import fire_and_forget, get_reaction_name


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

fastText = FastTextModel()

last_renote = time.time()

def get_reaction_vector(note: dict):
    total: int = np.sum(list(note["reactions"].values()))
    results = np.zeros(fastText.model.get_dimension(), dtype=np.float32)

    for reaction, cnt in note["reactions"].items():
        name = get_reaction_name(reaction)
        results += fastText.get_word_vector(name) * int(cnt) / total
    
    return results

def get_similarity(note: dict):
    total: int = np.sum(list(note["reactions"].values()))

    positive_reactions = [
        "tasukaru",
        "igyo",
        "naruhodo",
        "arigato",
        "benri",
        "sitteokou",
        "otoku"
    ]

    negative_reactions = [
        "fakenews",
        "kaibunsyo_itadakimasita",
        "kusa",
        "thinking_face",
        "sonnakotonai",
        "dosukebe",
    ]

    reaction_vec = get_reaction_vector(note)

    target_vec = fastText.get_word_vector("tiken")
    target_norm = np.linalg.norm(target_vec)

    for except_reaction in negative_reactions:
        target_vec -= fastText.get_word_vector(except_reaction) / len(negative_reactions) * 1.2

    for add_reaction in positive_reactions:
        target_vec += fastText.get_word_vector(add_reaction) / len(positive_reactions) * 2.5

    target_vec *= target_norm / np.linalg.norm(target_norm)

    score = reaction_vec @ target_vec / (np.linalg.norm(reaction_vec) * np.linalg.norm(target_vec))

    return score * (total - 1) / total

def should_renote(note: dict):
    if not note["reactions"]:
        return False
    
    similarity: float = get_similarity(note)
    res = bool(similarity >= np.cos(np.pi / 6))

    if res:
        logger.info(f"{note['id']} should be renote: {similarity}")
    else:
        logger.debug(f"{note['id']} should not be renote: {similarity}")

    fastText.update(note)

    return res


@fire_and_forget
def send(event: str, note: dict | None = None):
    global last_renote

    if event == "mention":
        res = process_query(note)
        logger.info(f"mention {note['id']}: {res}")

    elif event == "note":
        if not note["renoteId"] is None and note["text"] is None:
            note = note["renote"]
        
        if should_renote(note):
            res = renote(note)
            logger.info(f"note {note['id']}: {res}")

            if res == "successfully renoted":
                last_renote = time.time()
    
    elif event == "rerenote":
        last_renote = time.time()
        res = rerenote()
        logger.info(f"rerenote: {res}")


async def observer(ws_url: str, channels: dict[str, str]):
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
    
    rerenote_interval = 60 * 60 * 8 - 60 * 20 - 40
    
    async for ws in connect(ws_url):
        try:
            init()

            await connect_channels(ws, channels)

            async for data in ws:
                msg: Msg = json.loads(data)

                if not msg["type"] == "channel": continue

                channel = channels[msg["body"]["id"]]
                event: str = msg["body"]["type"]

                if channel == "main" and event == "mention" or event == "note":
                    note: dict = msg["body"]["body"]

                    send(event, note)
                
                if time.time() - last_renote > rerenote_interval:
                    send("rerenote")

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

    asyncio.run(observer(ws_url, channels))