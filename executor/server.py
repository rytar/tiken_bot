import json
import logging
import redis
from elasticsearch import Elasticsearch
from flask import Flask, request

from commands import process_query
from misskey_wrapper import MisskeyWrapper
from notes import runner


config = json.load("../config.json")
TOKEN = config["TOKEN"]
ES_PASS = config["ES_PASS"]

# set logger
logger = logging.getLogger(__name__)
logging.basicConfig(format="%(asctime)s %(levelname)s %(name)s: lines %(lineno)d: %(message)s", filename='executor.log', encoding='utf-8', level=logging.INFO)

connection_pool = redis.ConnectionPool(host="localhost", port=6379)
redis_client = redis.StrictRedis(connection_pool=connection_pool, decode_responses=False)

es = Elasticsearch(
    "https://localhost:9200",
    ca_certs="~/elasticsearch-8.7.1/config/certs/http_ca.crt",
    basic_auth=("elastic", ES_PASS)
)

msk = MisskeyWrapper("misskey.io", i=TOKEN, DEBUG=True)

app = Flask(__name__)

@app.route('/', methods=["POST"])
def root():
    req = request.get_json()
    event = req["type"]
    note = req["note"]

    logger.info(f"{event}: {note['id']}")

    if event == "note":
        runner(note, redis_client, es, msk)
    elif event == "mention":
        process_query(note, es, msk)

    return "accepted", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0")