"""Web search through Tavily (free: 1,000 credits/month, 1 credit per basic search).
Three sources share this file:
  web     - the open web (blogs, forums, Nigerian journals, anything)
  cad     - CAD / 3D-model sites (GrabCAD, Printables, Thingiverse, ...)
  guides  - build guides and tutorials (YouTube, Instructables, Hackaday)
Needs TAVILY_API_KEY in your .env file."""
import json, os, re, urllib.request
from .base import Result, register

CAD_SITES = ["grabcad.com", "printables.com", "thingiverse.com",
             "makerworld.com", "cults3d.com"]
GUIDE_SITES = ["youtube.com", "instructables.com", "hackaday.io"]

def _search(query, domains=None, limit=5):
    key = os.getenv("TAVILY_API_KEY")
    if not key:
        raise RuntimeError("TAVILY_API_KEY is not set in .env")
    payload = {"query": query, "max_results": limit, "search_depth": "basic"}
    if domains:
        payload["include_domains"] = domains
    req = urllib.request.Request(
        "https://api.tavily.com/search",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json",
                 "Authorization": "Bearer " + key})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r).get("results", [])

def _clean_url(url):
    """Link to the main page, not its comments / related tabs."""
    return re.sub(r"/(comments|related)/?$", "", url)

def _maker(title, content):
    """Best-effort: 'by NAME' in a CAD title, or 'Channel: NAME' for videos."""
    m = re.search(r"\bby ([\w][\w.\- ]{1,40}?)(?:\s*[|\u2013-]\s|\s*$)", title)
    if m:
        return m.group(1).strip()
    m = re.search(r"Channel:\s*(.+?)\s+[\d.,]+[KM]?\s+subscribers", content or "")
    return m.group(1).strip() if m else ""

def _results(items, source, kind):
    return [Result(i.get("title") or i["url"], _clean_url(i["url"]),
                   (i.get("content") or "")[:300], source, kind,
                   _maker(i.get("title") or "", i.get("content") or ""))
            for i in items]

@register("web")
def search_web(query, limit=5):
    return _results(_search(query, None, limit), "web", "page")

@register("cad")
def search_cad(query, limit=5):
    return _results(_search(query, CAD_SITES, limit), "cad", "cad-files")

@register("guides")
def search_guides(query, limit=5):
    return _results(_search(query + " build tutorial", GUIDE_SITES, limit),
                    "guides", "guide")
