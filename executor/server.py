import asyncio
import json
import logging
import redis
from elasticsearch import Elasticsearch
from flask import Flask, request

from commands import process_query
from misskey_wrapper import MisskeyWrapper
from notes import renote


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

def process(event: str, note: dict):
    if event == "note":
        renote(note, redis_client, es, msk)
    elif event == "mention":
        process_query(note, es, msk)

app = Flask(__name__)

@app.route('/', methods=["POST"])
def root():
    req = request.get_json()
    event = req["type"]
    note = req["note"]

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    loop.run_in_executor(None, process, event, note)

    return "accepted", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0")