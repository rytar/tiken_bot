import pickle
import redis
import requests
from elasticsearch import Elasticsearch
from misskey_wrapper import MisskeyWrapper

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

def should_renote(note: dict):
    res = requests.post("http://localhost:5001", json=note)
    data = res.json()
    return data["result"]

def runner(note: dict, redis_client: redis.Redis, es: Elasticsearch, msk: MisskeyWrapper):
    print(note)
    if not note["renoteId"] is None and note["text"] is None:
        note = note["renote"]
    
    if should_renote(note):
        renoted_ids = [ pickle.loads(key) for key in redis_client.hkeys("notes") ]
        if note["id"] in renoted_ids: return

        print(f"renote: {note['id']}")

        msk.notes_create(renote_id=note["id"])

        redis_client.hset("notes", pickle.dumps(note["id"]), pickle.dumps(note))
        
        text = get_text(note)
        es.index(index="notes", id=note["id"], document={"text": text, "id": note["id"]})