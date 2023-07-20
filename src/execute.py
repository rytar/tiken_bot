import datetime
import json
import logging
import numpy as np
import pickle
import redis
import regex
from elasticsearch import Elasticsearch
from misskey.enum import NoteVisibility
from misskey.exceptions import MisskeyAPIException
from tenacity import retry, wait_fixed, retry_if_exception_type

from misskey_wrapper import MisskeyWrapper
from utils import get_datetime, get_text

with open("./config.json") as f:
    config = json.loads(f.read())

TOKEN = config["TOKEN"]
ES_PASS = config["ES_PASS"]
DEBUG = config["DEBUG"]

# set logger
logger = logging.getLogger(__name__)

connection_pool = redis.ConnectionPool(host="localhost", port=6379)
redis_client = redis.StrictRedis(connection_pool=connection_pool, decode_responses=False)

es = Elasticsearch(
    "https://localhost:9200",
    ca_certs="~/elasticsearch-8.7.1/config/certs/http_ca.crt",
    basic_auth=("elastic", ES_PASS)
)

msk = MisskeyWrapper("misskey.io", i=TOKEN, DEBUG=DEBUG)

# reset Redis DB about renoted notes
def message_if_retry(state):
    print(state)
    print("Resetting DB was failed. It will be retried after 30s.")

@retry(wait=wait_fixed(30), retry=retry_if_exception_type(MisskeyAPIException), after=message_if_retry)
def init():
    redis_client.flushall()

    logger.info("initializing...")

    MY_ID = msk.i()["id"]

    until_datetime = datetime.datetime.now(tz=datetime.timezone.utc)

    notes = msk.users_notes(MY_ID, include_replies=False, limit=100, until_date=until_datetime)

    while len(notes) != 0:
        for note in notes:
            until_datetime = get_datetime(note["createdAt"])

            # RNならDBに保存
            if not note["renoteId"] is None and note["text"] is None:
                renoted_note = note["renote"]

                # 多重RNならRN解除
                renoted_ids = [ pickle.loads(key) for key in redis_client.hkeys("notes") ]
                if renoted_note["id"] in renoted_ids:
                    msk.notes_delete(note["id"])
                else:
                    redis_client.hset("notes", pickle.dumps(renoted_note["id"]), pickle.dumps(renoted_note))
                    redis_client.hset("renotes", pickle.dumps(renoted_note["id"]), pickle.dumps(note["id"]))

                    text = get_text(renoted_note)
                    es.index(index="notes", id=renoted_note["id"], document={"text": text, "id": renoted_note["id"]})
                    
            else:
                # 元ノートが削除されたものもRN解除
                if note["text"] is None:
                    msk.notes_delete(note["id"])

        notes = msk.users_notes(MY_ID, include_replies=False, limit=100, until_date=until_datetime)

    logger.info("success")

def renote(note: dict):
    renoted_ids = [ pickle.loads(key) for key in redis_client.hkeys("notes") ]
    if note["id"] in renoted_ids:
        logger.info("already renoted")
        return "already renoted"

    logger.info(f"should renote: {note['id']}")

    redis_client.hset("notes", pickle.dumps(note["id"]), pickle.dumps(note))
    
    text = get_text(note)
    es.index(index="notes", id=note["id"], document={"text": text, "id": note["id"]})
    
    res = msk.notes_create(renote_id=note["id"])
    created_note = res["createdNote"]

    redis_client.hset("renotes", pickle.dumps(note["id"]), pickle.dumps(created_note["id"]))

    logger.info(f"{created_note['id']} renoted: {note['id']}")

    return "successfully renoted"

def rerenote():
    renoted_ids = [ pickle.loads(key) for key in redis_client.hkeys("notes") ]
    renotes = { pickle.loads(key): pickle.loads(redis_client.hget("renotes", key)) for key in redis_client.hkeys("renotes") }

    picked_id = np.random.choice(renoted_ids)
    note_id = renotes[picked_id]

    logger.info(f"delete renote {note_id} that be referring to {picked_id}")
    msk.notes_delete(note_id)

    res = msk.notes_create(renote_id=picked_id)
    created_note = res["createdNote"]

    redis_client.hset("renotes", pickle.dumps(picked_id), pickle.dumps(created_note["id"]))

    logger.info(f"{created_note['id']} rerenote {picked_id}")

    return f"successfully rerenoted {picked_id}"

# function for processing query
query_counts = 0
query_timestamp = None

user_mention = regex.compile(r"\s*@[^\s]+(@[\s]+)?\s*")
cmd_pattern = regex.compile(r"^\s*/([^\s]+)[\s\n]+(.+)?$", regex.DOTALL)
word_group_pattern = regex.compile(r"\s*\|\s*")
word_pattern = regex.compile(r"\s+")

def process_query(note: dict) -> str:
    global query_counts, query_timestamp

    # botには反応しない
    if note["user"]["isBot"]: return "user is bot"

    is_direct = note["visibility"] == "specified"
    user_id = note["userId"]

    command = user_mention.sub('', note["text"]).strip() + '\n'

    logger.info(f"userId: {user_id}, isDirect: {is_direct}, cmd: {command}")

    m = cmd_pattern.match(command)
    if m is None:
        # misskey_notes_create(text="入力形式が正しくありません。`/command args`の形で入力してください。", visibility="specified", visible_user_ids=[user_id], reply_id=note["id"])
        return "invalid format"

    # コマンド利用のレートリミット設定（10クエリ/秒）
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    if query_timestamp is None:
        query_timestamp = now
    elif (now - query_timestamp).seconds >= 1:
        query_counts = 0
        query_timestamp = now

    if query_counts >= 10:
        msk.notes_create(
            text="コマンド利用のレートリミット（10クエリ/秒）に達しました。もう一度お試しください。",
            visibility=NoteVisibility.SPECIFIED if is_direct else NoteVisibility.PUBLIC,
            visible_user_ids=[user_id] if is_direct else None,
            reply_id=note["id"]
        )
        return "rate limit"

    query_counts += 1
    
    cmd, arg = m.groups()

    if cmd == "ping":
        logger.info("get ping")

        msk.notes_create(
            text="pong!",
            visibility=NoteVisibility.SPECIFIED if is_direct else NoteVisibility.PUBLIC,
            visible_user_ids=[user_id] if is_direct else None,
            reply_id=note["id"]
        )

        logger.info("return pong")

    elif cmd == "search":
        if arg == None:
            msk.notes_create(
                text="`/search`コマンドを利用する際は検索したい文字列を指定してください。",
                visibility=NoteVisibility.SPECIFIED if is_direct else NoteVisibility.PUBLIC,
                visible_user_ids=[user_id] if is_direct else None,
                reply_id=note["id"]
            )
            return "search keywords were not found"

        arg = arg.strip()
        logger.info(f"get search query: {arg}")

        res = es.search(index="notes", query={"match": {"text": arg}})

        hit_cnt = res["hits"]["total"]["value"]

        result_cw = None
        result_str = ''

        if hit_cnt == 0:
            result_str = f"検索キーワード`{arg}`に関連するノートが見つかりませんでした。\n"
        else:
            scores = [ hit["_score"] for hit in res["hits"]["hits"] ]
            results = [ hit["_source"] for hit in res["hits"]["hits"] ]
            
            cnt = np.sum(np.array(scores) >= np.max(scores) * 0.8)

            logger.info(f"hit {hit_cnt} notes")
            logger.info(f"score: max: {np.max(scores):.3f}, th: {np.max(scores) * 0.8:.3f}, min: {np.min(scores):.3f}")

            results = results[:int(cnt)]
            result_ids = [ res["id"] for res in results ]

            result_cw = f"検索キーワード`{arg}`に関連するノートが{len(result_ids)}件見つかりました。\n"
            result_str = '\n'.join([ f"https://misskey.io/notes/{id}" for id in result_ids ])
        
        msk.notes_create(
            text=result_str,
            cw=result_cw,
            visibility=NoteVisibility.SPECIFIED if is_direct else NoteVisibility.PUBLIC,
            visible_user_ids=[user_id] if is_direct else None,
            reply_id=note["id"]
        )
        logger.info(f"return {len(result_ids)} links")

    else:
        msk.notes_create(
            text=f"コマンド{cmd}は存在しません。",
            visibility=NoteVisibility.SPECIFIED if is_direct else NoteVisibility.PUBLIC,
            visible_user_ids=[user_id] if is_direct else None,
            reply_id=note["id"]
        )

        return "the command is not exist"
    
    return "successfully processed the query"
