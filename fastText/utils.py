import emoji
import regex

def get_reaction_name(reaction: str):
    m = regex.fullmatch(r"^:([^:@]+)@([^@:]+):$", reaction)
    if m:
        return m.groups()[0]
    elif emoji.is_emoji(reaction):
        return emoji.demojize(reaction)[1:-1]
    else:
        return None