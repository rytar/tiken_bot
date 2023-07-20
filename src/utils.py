import asyncio
import datetime
import emoji
import regex

def fire_and_forget(func):
    def wrapper(*args, **kwargs):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_in_executor(None, func, *args, *kwargs)
    return wrapper

def get_datetime(createdAt: str):
    return datetime.datetime.strptime(createdAt, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=datetime.timezone.utc)

def get_reaction_name(reaction: str):
    m = regex.fullmatch(r"^:([^:@]+)@([^@:]+):$", reaction)
    if m:
        return m.groups()[0]
    elif emoji.is_emoji(reaction):
        return emoji.demojize(reaction)[1:-1]
    else:
        return None
    
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
