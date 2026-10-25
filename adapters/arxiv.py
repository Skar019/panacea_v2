import urllib.parse
import xml.etree.ElementTree as ET
import net
from .base import Result, register

NS = {"a": "http://www.w3.org/2005/Atom"}

@register("arxiv")
def search_arxiv(query, limit=5):
    url = ("http://export.arxiv.org/api/query?search_query=all:"
           + urllib.parse.quote(query) + f"&max_results={limit}")
    root = ET.fromstring(net.get(url))
    out = []
    for e in root.findall("a:entry", NS):
        names = [a.find("a:name", NS).text.strip() for a in e.findall("a:author", NS)]
        who = names[0] + (" et al." if len(names) > 1 else "") if names else ""
        link = ("https://arxiv.org/search/?searchtype=author&query="
                + urllib.parse.quote(names[0])) if names else ""
        out.append(Result(
            e.find("a:title", NS).text.strip().replace("\n", " "),
            e.find("a:id", NS).text.strip(),
            e.find("a:summary", NS).text.strip()[:300],
            "arxiv", "paper", who, link))
    return out
