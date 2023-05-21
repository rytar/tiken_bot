import emoji
import regex

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

def get_reaction_name(reaction: str):
    m = regex.fullmatch(r"^:([^:@]+)@([^@:]+):$", reaction)
    if m:
        return m.groups()[0]
    elif emoji.is_emoji(reaction):
        return emoji.demojize(reaction)[1:-1]
    else:
        return None