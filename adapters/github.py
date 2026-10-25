import os, urllib.parse
import net
from .base import Result, register

@register("github")
def search_github(query, limit=5):
    url = ("https://api.github.com/search/repositories?q="
           + urllib.parse.quote(query) + f"&sort=stars&per_page={limit}")
    headers = {"Accept": "application/vnd.github+json"}
    if os.getenv("GITHUB_TOKEN"):
        headers["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]
    items = net.get_json(url, headers)["items"]
    return [Result(i["full_name"], i["html_url"], i["description"] or "",
                   "github", "repo", i["owner"]["login"], i["owner"]["html_url"])
            for i in items]
