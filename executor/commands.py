import datetime
import logging
import numpy as np
import regex
from elasticsearch import Elasticsearch
from misskey.enum import NoteVisibility

from misskey_wrapper import MisskeyWrapper


# set logger
logger = logging.getLogger(__name__)

# function for processing query
query_counts = 0
query_timestamp = None

user_mention = regex.compile(r"\s*@[^\s]+(@[\s]+)?\s*")
cmd_pattern = regex.compile(r"^\s*/([^\s]+)[\s\n]+(.+)?$", regex.DOTALL)
word_group_pattern = regex.compile(r"\s*\|\s*")
word_pattern = regex.compile(r"\s+")

def process_query(note: dict, es: Elasticsearch, msk: MisskeyWrapper):
    global query_counts, query_timestamp

    # botには反応しない
    if note["user"]["isBot"]: return

    is_direct = note["visibility"] == "specified"
    user_id = note["userId"]

    command = user_mention.sub('', note["text"]).strip() + '\n'

    logger.info(f"userId: {user_id}, isDirect: {is_direct}, cmd: {command}")

    m = cmd_pattern.match(command)
    if m is None:
        # misskey_notes_create(text="入力形式が正しくありません。`/command args`の形で入力してください。", visibility="specified", visible_user_ids=[user_id], reply_id=note["id"])
        return

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
        return

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
            return

        arg = arg.strip()
        logger.info(f"get search query: {arg}")

        res = es.search(index="notes", query={"match": {"text": arg}})

        hit_cnt = res["hits"]["total"]["value"]

        result_cw = None
        result_str = ''

        if hit_cnt == 0:
            result_str = f"検索キーワード`{arg}`に関連するノートが見つかりませんでした。\n"
        else:
            results = []
            scores = []

            for hit in res["hits"]["hits"]:
                scores.append(hit["_score"])
                results.append(hit["_source"])
            
            mean = np.mean(scores)
            std = np.std(scores)
            cnt = np.sum(np.array(scores) >= mean + 0.5 * std)

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
