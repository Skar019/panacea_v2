from dataclasses import dataclass

ADAPTERS = {}


@dataclass
class Result:
    title: str
    url: str
    summary: str
    source: str
    kind: str
    creator: str = ""
    creator_url: str = ""
    why: str = ""


def register(name):
    def wrap(fn):
        ADAPTERS[name] = fn
        return fn
    return wrap
