import json

with open("./config.json") as f:
    config = json.loads(f.read())

TOKEN = config["TOKEN"]
ES_PASS = config["ES_PASS"]
DEBUG = config["DEBUG"]