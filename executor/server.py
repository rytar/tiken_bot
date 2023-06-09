import json
import logging
import redis
from elasticsearch import Elasticsearch
from flask import Flask, request

from commands import process_query
from misskey_wrapper import MisskeyWrapper
from notes import renote, rerenote


with open("../config.json") as f:
    config = json.loads(f.read())

TOKEN = config["TOKEN"]
ES_PASS = config["ES_PASS"]
DEBUG = config["DEBUG"]

# set logger
logger = logging.getLogger(__name__)
logging.basicConfig(format="%(asctime)s %(levelname)s %(name)s: lines %(lineno)d: %(message)s", filename="./executor.log", encoding="utf-8", level=logging.INFO)

connection_pool = redis.ConnectionPool(host="localhost", port=6379)
redis_client = redis.StrictRedis(connection_pool=connection_pool, decode_responses=False)

es = Elasticsearch(
    "https://localhost:9200",
    ca_certs="~/elasticsearch-8.7.1/config/certs/http_ca.crt",
    basic_auth=("elastic", ES_PASS)
)

msk = MisskeyWrapper("misskey.io", i=TOKEN, DEBUG=DEBUG)

def process(event: str, note: dict | None):
    if event == "note":
        return renote(note, redis_client, es, msk)
    elif event == "mention":
        return process_query(note, es, msk)
    elif event == "rerenote":
        return rerenote(redis_client, msk)
    else:
        return "unknown event"

app = Flask(__name__)

@app.route('/', methods=["POST"])
def post():
    req = request.get_json()
    event = req["event"]

    logger.info(f"event: {event}")

    if event == "rerenote":
        note = None
    else:
        note = req["note"]
        logger.info(f"{event}: {note['id']}")

    status = process(event, note)

    return status, 200

if __name__ == "__main__":
    app.run(host="0.0.0.0")