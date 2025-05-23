NICKNAME_MAP = {
    "michael": ["mike", "mic", "mikey"],
    "john": ["johnny", "johnd", "jdoe", "jon"],
    "elizabeth": ["liz", "beth", "liza"],
    "robert": ["rob", "bobby", "bob"],
    "william": ["bill", "will", "willy"],
    "jennifer": ["jen", "jenny", "j"],
    "alexander": ["alex", "xander", "lex"],
    "christopher": ["chris", "topher"],
    "daniel": ["dan", "danny"],
    "stephanie": ["steph", "steffi"],
    "linus": ["linux", "lino", "lin"],
}

SURNAME_MAP = {
    "müller": ["mueller", "miller", "mueler", "mue"],
    "schmidt": ["schmid", "schmitt", "smit", "smidt"],
    "meier": ["meyer", "maier", "mayr", "meyr"],
    "bauer": ["baur", "bayer"],
    "hoffmann": ["hofmann", "hofman", "hoffman"],
    "weber": ["weaver", "webr"],
    "fischer": ["fisher", "fichr"],
}

def get_nicknames(name: str) -> list:
    name = name.lower().strip()
    return NICKNAME_MAP.get(name, [])

def get_surname_variants(name: str) -> list:
    name = name.lower().strip()
    return SURNAME_MAP.get(name, [])
