import redis
from elasticsearch import Elasticsearch
from flask import Flask, request

from commands import process_query
from config import TOKEN, ES_PASS
from misskey_wrapper import MisskeyWrapper
from notes import runner


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
    event = request.form.get("type", '', type=str)
    note = request.form.get("note", {}, type=dict)

    if event == "note":
        runner(note, redis_client, es, msk)
    elif event == "mention":
        process_query(note, es, msk)

    return "accepted", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0")