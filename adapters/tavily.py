"""Web search through Tavily (free: 1,000 credits/month, 1 credit per basic search).
Four sources share this file:
  web    the open web (blogs, forums, Nigerian journals, anything)
  cad    CAD/3D-model sites (GrabCAD, Printables, Thingiverse, ...)
  guides build guides and tutorials (YouTube, Instructables, Hackaday)
  social developer/maker posts on X (Twitter), TikTok, Instagram, and Reddit
Needs TAVILY_API_KEY in your .env file."""
import json
import os
import re
import urllib.request
from .base import Result, register

CAD_SITES = [
    "grabcad.com",
    "printables.com",
    "thingiverse.com",
    "makerworld.com",
    "cults3d.com",
]

GUIDE_SITES = [
    "youtube.com",
    "instructables.com",
    "hackaday.io",
]

SOCIAL_SITES = [
    "x.com",
    "twitter.com",
    "tiktok.com",
    "instagram.com",
    "reddit.com",
]


def _search(query, domains=None, limit=5):
    key = os.environ.get("TAVILY_API_KEY")
    if not key:
        raise RuntimeError("TAVILY_API_KEY is not set in .env")
    payload = {
        "query": query,
        "max_results": limit,
        "search_depth": "basic",
    }
    if domains:
        payload["include_domains"] = domains
    req = urllib.request.Request(
        "https://api.tavily.com/search",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8")).get("results", [])


def _clean_url(url):
    """Link to the main page, not its comments / related tabs."""
    return re.sub(r"/(comments|related)/?$", "", url or "")


def _maker(title, content, url=""):
    """Best-effort: extract @handle or u/username from social URLs first,
    then 'by NAME' in a CAD title, or 'Channel: NAME' for videos."""
    u = url or ""
    # 1. X / Twitter handle from URL: x.com/handle/status/...
    m_x = re.search(r"(?:x\.com|twitter\.com)/([A-Za-z0-9_]{1,15})(?:/|$)", u)
    if m_x and m_x.group(1).lower() not in ("i", "intent", "search", "hashtag", "home", "explore"):
        handle = m_x.group(1)
        return f"@{handle} (X)", f"https://x.com/{handle}"

    # 2. TikTok handle from URL: tiktok.com/@handle/...
    m_tt = re.search(r"tiktok\.com/@([A-Za-z0-9_.]+)", u)
    if m_tt:
        handle = m_tt.group(1)
        return f"@{handle} (TikTok)", f"https://www.tiktok.com/@{handle}"

    # 3. Reddit subreddit or user from URL
    m_rd_user = re.search(r"reddit\.com/user/([A-Za-z0-9_-]+)", u)
    if m_rd_user:
        user = m_rd_user.group(1)
        return f"u/{user} (Reddit)", f"https://www.reddit.com/user/{user}"
    m_rd_sub = re.search(r"reddit\.com/r/([A-Za-z0-9_]+)", u)
    if m_rd_sub:
        sub = m_rd_sub.group(1)
        return f"r/{sub} (Reddit)", f"https://www.reddit.com/r/{sub}"

    # 4. Instagram handle from URL (if profile/reel URL includes username)
    m_ig = re.search(r"instagram\.com/([A-Za-z0-9_.]+)(?:/|$)", u)
    if m_ig and m_ig.group(1).lower() not in ("p", "reel", "reels", "tv", "explore", "stories"):
        handle = m_ig.group(1)
        return f"@{handle} (Instagram)", f"https://www.instagram.com/{handle}/"

    # 5. CAD 'by NAME' in title
    m_cad = re.search(
        r"\bby\s+([\w][\w.\- ]{1,30}?)(?:\s*[|\u2013\-]|\s+on\s+|$)",
        title or "",
        re.I,
    )
    if m_cad:
        return m_cad.group(1).strip(), ""

    # 6. YouTube 'Channel: NAME ... subscribers'
    m_yt = re.search(
        r"Channel:\s*(.+?)\s+[\d.,]+[KM]?\s+subscribers",
        content or "",
    )
    if m_yt:
        return m_yt.group(1).strip(), ""

    return "", ""


def _results(items, source, kind):
    out = []
    for it in items:
        raw_url = _clean_url(it.get("url") or "")
        title = it.get("title") or raw_url
        content = (it.get("content") or "")[:300]
        creator, creator_url = _maker(title, content, raw_url)
        out.append(
            Result(
                title=title,
                url=raw_url,
                summary=content,
                source=source,
                kind=kind,
                creator=creator,
                creator_url=creator_url,
            )
        )
    return out


@register("web")
def search_web(query, limit=5):
    return _results(_search(query, None, limit), "web", "page")


@register("cad")
def search_cad(query, limit=5):
    return _results(_search(query, CAD_SITES, limit), "cad", "cad-files")


@register("guides")
def search_guides(query, limit=5):
    return _results(
        _search(f"{query} build tutorial", GUIDE_SITES, limit),
        "guides",
        "guide",
    )


@register("social")
def search_social(query, limit=5):
    return _results(
        _search(f"{query} project build", SOCIAL_SITES, limit),
        "social",
        "social-post",
    )
