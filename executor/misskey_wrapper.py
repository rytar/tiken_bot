import datetime
import logging
import time
from misskey import Misskey
from misskey.enum import NoteVisibility
from misskey.exceptions import MisskeyAPIException
from tenacity import retry, wait_fixed, retry_if_exception_type
from requests import Session
from requests.exceptions import Timeout, JSONDecodeError, ConnectionError

class MisskeyWrapper:

    __DEFAULT_ADDRESS = "misskey.io"
    
    def __init__(self, address:str = __DEFAULT_ADDRESS, i: str | None = None, session: Session | None = None, DEBUG = True):
        self.msk = Misskey(address=address, i=i, session=session)

        self.access_cooltime = 1
        self.DEBUG = DEBUG
        self.logger = logging.getLogger(__name__)

    
    @retry(wait=wait_fixed(2), retry=retry_if_exception_type((Timeout, JSONDecodeError, ConnectionError, MisskeyAPIException)))
    def i(self):
        result = self.msk.i()
        time.sleep(self.access_cooltime)
        return result

    @retry(wait=wait_fixed(2), retry=retry_if_exception_type((Timeout, JSONDecodeError, ConnectionError)))
    def users_notes(
        self,
        user_id: str,
        include_replies: bool = True,
        limit: int = 10,
        since_id: str | None = None,
        until_id: str | None = None,
        since_date: datetime.datetime | int | None = None,
        until_date: datetime.datetime | int | None = None,
        include_my_renotes: bool = True,
        with_files: bool = False,
        file_type: list[str] | None = None,
        exclude_nsfw: bool = False
    ):
        result = self.msk.users_notes(
            user_id=user_id,
            include_replies=include_replies,
            limit=limit,
            since_id=since_id,
            until_id=until_id,
            since_date=since_date,
            until_date=until_date,
            include_my_renotes=include_my_renotes,
            with_files=with_files,
            file_type=file_type,
            exclude_nsfw=exclude_nsfw
        )
        time.sleep(self.access_cooltime)
        return result

    @retry(wait=wait_fixed(2), retry=retry_if_exception_type((Timeout, JSONDecodeError, ConnectionError)))
    def notes_delete(self, note_id: str):
        if self.DEBUG:
            self.logger.debug(f"delete https://misskey.io/notes/{note_id}")
            return
        
        try:
            result = self.msk.notes_delete(note_id)
            time.sleep(self.access_cooltime * 2)
            return result
        except MisskeyAPIException as e:
            self.logger.error(f"{type(e)}: {e}")
        
        time.sleep(self.access_cooltime)
    
    @retry(wait=wait_fixed(2), retry=retry_if_exception_type((Timeout, JSONDecodeError, ConnectionError)))
    def notes_create(
        self,
        text: str | None = None,
        cw: str | None = None,
        visibility: NoteVisibility | str = NoteVisibility.PUBLIC,
        visible_user_ids: list[str] | None = None,
        via_mobile: bool = False,
        local_only: bool = False,
        no_extract_mentions: bool = False,
        no_extract_hashtags: bool = False,
        no_extract_emojis: bool = False,
        file_ids: list[str] | None = None,
        reply_id: str | None = None,
        renote_id: str | None = None,
        poll_choices: list[str] | tuple[str] | None = None,
        poll_multiple: bool = False,
        poll_expires_at: int | datetime.datetime | None = None,
        poll_expired_after: int | datetime.timedelta | None = None
    ):
        if self.DEBUG:
            self.logger.debug("create note")
            self.logger.debug(f"  cw: {cw}")
            self.logger.debug(f"  text: {text}")
            self.logger.debug(f"  renote: {renote_id}")
            return
        
        try:
            result = self.msk.notes_create(
                text=text,
                cw=cw,
                visibility=visibility,
                visible_user_ids=visible_user_ids,
                via_mobile=via_mobile,
                local_only=local_only,
                no_extract_mentions=no_extract_mentions,
                no_extract_hashtags=no_extract_hashtags,
                no_extract_emojis=no_extract_emojis,
                file_ids=file_ids,
                reply_id=reply_id,
                renote_id=renote_id,
                poll_choices=poll_choices,
                poll_multiple=poll_multiple,
                poll_expires_at=poll_expires_at,
                poll_expired_after=poll_expired_after
            )
            time.sleep(self.access_cooltime)
            return result
        except MisskeyAPIException as e:
            self.logger.error(f"{type(e)}: {e}")
            pass

        time.sleep(self.access_cooltime)

    @retry(wait=wait_fixed(2), retry=retry_if_exception_type((Timeout, JSONDecodeError, ConnectionError)))
    def notes_show(self, note_id: str):
        try:
            result = self.msk.notes_show(note_id)
            time.sleep(self.access_cooltime)
            return result
        except MisskeyAPIException as e:
            self.logger.error(f"{type(e)}: {e}")
            pass

        time.sleep(self.access_cooltime)