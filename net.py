import json, urllib.request

def get(url, headers=None, timeout=20):
    h = {"User-Agent": "Panacea/0.2 (student project)"}
    h.update(headers or {})
    req = urllib.request.Request(url, headers=h)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8")

def get_json(url, headers=None):
    return json.loads(get(url, headers))
