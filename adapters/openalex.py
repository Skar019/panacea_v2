import os, urllib.parse
import net
from .base import Result, register

def _abstract(inv):
    """OpenAlex stores abstracts as {word: [positions]}; rebuild the text."""
    if not inv:
        return ""
    words = {}
    for w, positions in inv.items():
        for p in positions:
            words[p] = w
    return " ".join(words[i] for i in sorted(words))

def _lead(authorships):
    """(name, profile link) of the corresponding author, else the first."""
    if not authorships:
        return "", ""
    lead = next((a for a in authorships if a.get("is_corresponding")), authorships[0])
    who = lead.get("author") or {}
    name = who.get("display_name") or ""
    inst = (lead.get("institutions") or [{}])[0].get("display_name")
    if name and inst:
        name += f" ({inst})"
    if name and len(authorships) > 1:
        name += " et al."
    return name, who.get("orcid") or who.get("id") or ""

@register("openalex")
def search_openalex(query, limit=5):
    url = ("https://api.openalex.org/works?search=" + urllib.parse.quote(query)
           + f"&per-page={limit}"
           + "&select=id,display_name,doi,publication_year,abstract_inverted_index,authorships")
    if os.getenv("OPENALEX_EMAIL"):          # optional, gives faster service
        url += "&mailto=" + urllib.parse.quote(os.environ["OPENALEX_EMAIL"])
    out = []
    for w in net.get_json(url).get("results", []):
        name, link = _lead(w.get("authorships"))
        out.append(Result(f'{w["display_name"]} ({w.get("publication_year")})',
                          w.get("doi") or w["id"],
                          _abstract(w.get("abstract_inverted_index"))[:300],
                          "openalex", "paper", name, link))
    return out
