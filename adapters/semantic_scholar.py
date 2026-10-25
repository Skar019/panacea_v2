import os, time, urllib.parse
import net
from .base import Result, register

@register("semantic_scholar")
def search_semantic_scholar(query, limit=5):
    time.sleep(1)   # free tier is strict about speed
    url = ("https://api.semanticscholar.org/graph/v1/paper/search?query="
           + urllib.parse.quote(query)
           + f"&limit={limit}&fields=title,url,abstract,year,authors")
    headers = {}
    if os.getenv("S2_API_KEY"):
        headers["x-api-key"] = os.environ["S2_API_KEY"]
    data = net.get_json(url, headers).get("data", [])
    out = []
    for p in data:
        authors = p.get("authors") or []
        name = authors[0]["name"] + (" et al." if len(authors) > 1 else "") if authors else ""
        link = (f"https://www.semanticscholar.org/author/{authors[0]['authorId']}"
                if authors and authors[0].get("authorId") else "")
        out.append(Result(f'{p["title"]} ({p.get("year")})', p["url"],
                          (p.get("abstract") or "")[:300],
                          "semantic_scholar", "paper", name, link))
    return out
