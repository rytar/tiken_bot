import logging
import numpy as np
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
    if note["id"] in renoted_ids:
        logger.info("already renoted")
        return "already renoted"

    logger.info(f"should renote: {note['id']}")

    redis_client.hset("notes", pickle.dumps(note["id"]), pickle.dumps(note))
    
    text = get_text(note)
    es.index(index="notes", id=note["id"], document={"text": text, "id": note["id"]})
    
    created_note = msk.notes_create(renote_id=note["id"])

    redis_client.hset("renotes", pickle.dumps(note["id"]), pickle.dumps(created_note["id"]))

    logger.info(f"renoted: {note['id']}")

    return "successfully renoted"

def rerenote(redis_client: redis.Redis, msk: MisskeyWrapper):
    renoted_ids = [ pickle.loads(key) for key in redis_client.hkeys("notes") ]
    renotes = { pickle.loads(key): pickle.loads(redis_client.hget("renotes", key)) for key in redis_client.hkeys("renotes") }

    picked_id = np.random.choice(renoted_ids)
    note_id = renotes[picked_id]

    logger.info(f"delete renote {note_id} that be referring to {picked_id}")
    msk.notes_delete(note_id)

    logger.info(f"rerenote {picked_id}")
    created_note = msk.notes_create(renote_id=picked_id)
    redis_client.hset("renotes", pickle.dumps(picked_id), pickle.dumps(created_note["id"]))

    return f"successfully rerenoted {picked_id}"