import datetime
import json
import logging
import pickle
import redis
from elasticsearch import Elasticsearch
from misskey.exceptions import MisskeyAPIException
from tenacity import retry, wait_fixed, retry_if_exception_type

from misskey_wrapper import MisskeyWrapper


# set logger
logger = logging.getLogger(__name__)
logging.basicConfig(format="%(asctime)s %(levelname)s %(name)s: lines %(lineno)d: %(message)s", filename="./init.log", encoding="utf-8", level=logging.INFO)


with open("../config.json") as f:
    config = json.loads(f.read())

TOKEN = config["TOKEN"]
ES_PASS = config["ES_PASS"]
DEBUG = config["DEBUG"]

def get_datetime(createdAt: str):
    return datetime.datetime.strptime(createdAt, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=datetime.timezone.utc)

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


# reset Redis DB about renoted notes
def message_if_retry(state):
    print(state)
    print("resetting DB was failed. retry after 30 sec.")

@retry(wait=wait_fixed(30), retry=retry_if_exception_type(MisskeyAPIException), after=message_if_retry)
def init(redis_client: redis.StrictRedis, es: Elasticsearch, msk: MisskeyWrapper):
    redis_client.flushall()

    print("reset DB")

    MY_ID = msk.i()["id"]

    until_datetime = datetime.datetime.now(tz=datetime.timezone.utc)

    notes = msk.users_notes(MY_ID, include_replies=False, limit=100, until_date=until_datetime)
    print(f"get {len(notes)} notes")

    while len(notes) != 0:
        for note in notes:
            until_datetime = get_datetime(note["createdAt"])

            # RNならDBに保存
            if not note["renoteId"] is None and note["text"] is None:
                renoted_note = note["renote"]

                # 条件を満たしていない or 多重RNならRN解除
                renoted_ids = [ pickle.loads(key) for key in redis_client.hkeys("notes") ]
                if renoted_note["id"] in renoted_ids:
                    msk.notes_delete(note["id"])
                else:
                    redis_client.hset("notes", pickle.dumps(renoted_note["id"]), pickle.dumps(renoted_note))

                    text = get_text(renoted_note)
                    es.index(index="notes", id=renoted_note["id"], document={"text": text, "id": renoted_note["id"]})
                    
            else:
                # 元ノートが削除されたものもRN解除
                if note["text"] is None:
                    msk.notes_delete(note["id"])

        notes = msk.users_notes(MY_ID, include_replies=False, limit=100, until_date=until_datetime)
        print(f"get {len(notes)} notes")

if __name__ == "__main__":
    connection_pool = redis.ConnectionPool(host="localhost", port=6379)
    redis_client = redis.StrictRedis(connection_pool=connection_pool, decode_responses=False)

    es = Elasticsearch(
        "https://localhost:9200",
        ca_certs="~/elasticsearch-8.7.1/config/certs/http_ca.crt",
        basic_auth=("elastic", ES_PASS),
        request_timeout=30, max_retries=10, retry_on_timeout=True
    )

    msk = MisskeyWrapper("misskey.io", i=TOKEN, DEBUG=DEBUG)

    init(redis_client, es, msk)