import logging
import pickle
import redis
from elasticsearch import Elasticsearch
from misskey_wrapper import MisskeyWrapper


# set logger
logger = logging.getLogger(__name__)

def get_text(note: dict):
    text: str = ''

    if note["cw"] is not None:
        text += note["cw"] + '\n'
    
    if note["text"] is not None:
        text += note["text"] + '\n'

    if note["renoteId"] is not None:
        if note["renote"]["cw"] is not None:
            text += note["renote"]["cw"] + '\n'

        if note["renote"]["text"] is not None:
            text += note["renote"]["text"] + '\n'
    
    return text

def renote(note: dict, redis_client: redis.Redis, es: Elasticsearch, msk: MisskeyWrapper):
    renoted_ids = [ pickle.loads(key) for key in redis_client.hkeys("notes") ]
    if note["id"] in renoted_ids: return

    logger.info(f"renote: {note['id']}")

    redis_client.hset("notes", pickle.dumps(note["id"]), pickle.dumps(note))
    
    text = get_text(note)
    es.index(index="notes", id=note["id"], document={"text": text, "id": note["id"]})
    
    msk.notes_create(renote_id=note["id"])

    logger.info(f"renoted: {note['id']}")