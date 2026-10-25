import urllib.parse
import net
from .base import Result, register

BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"

@register("pubmed")
def search_pubmed(query, limit=5):
    ids = net.get_json(BASE + "esearch.fcgi?db=pubmed&retmode=json&retmax="
                       + str(limit) + "&term=" + urllib.parse.quote(query)
                       )["esearchresult"]["idlist"]
    if not ids:
        return []
    summ = net.get_json(BASE + "esummary.fcgi?db=pubmed&retmode=json&id="
                        + ",".join(ids))["result"]
    out = []
    for i in ids:
        if i not in summ:
            continue
        authors = summ[i].get("authors") or []
        name = authors[0].get("name", "") if authors else ""
        link = ("https://pubmed.ncbi.nlm.nih.gov/?term="
                + urllib.parse.quote(name + "[Author]")) if name else ""
        if name and len(authors) > 1:
            name += " et al."
        out.append(Result(summ[i]["title"], f"https://pubmed.ncbi.nlm.nih.gov/{i}/",
                          summ[i].get("source", ""), "pubmed", "paper", name, link))
    return out
