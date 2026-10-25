import os
import urllib.parse
import net
from .base import Result, register


@register("unpaywall")
def search_unpaywall(query, limit=5):
    out = []
    email = os.environ.get("OPENALEX_EMAIL") or os.environ.get("UNPAYWALL_EMAIL") or "student@lasu.edu.ng"
    
    dois = []
    q_clean = query.strip()
    if q_clean.startswith("10.") and "/" in q_clean:
        dois.append(q_clean)
    else:
        oa_url = f"https://api.openalex.org/works?search={urllib.parse.quote(query)}&per-page={limit}&select=id,display_name,doi,primary_location,open_access,authorships"
        if email:
            oa_url += f"&mailto={urllib.parse.quote(email)}"
        data = net.get_json(oa_url)
        if data and isinstance(data, dict):
            for work in data.get("results", []):
                doi_full = work.get("doi") or ""
                if doi_full:
                    doi = doi_full.replace("https://doi.org/", "").strip()
                    if doi:
                        dois.append(doi)

    for doi in dois[:limit]:
        try:
            up_url = f"https://api.unpaywall.org/v2/{urllib.parse.quote(doi)}?email={urllib.parse.quote(email)}"
            res = net.get_json(up_url)
            if res and isinstance(res, dict) and res.get("is_oa"):
                title = res.get("title") or doi
                best_oa = res.get("best_oa_location") or {}
                pdf_url = best_oa.get("url_for_pdf") or best_oa.get("url") or f"https://doi.org/{doi}"
                
                authors = res.get("z_authors") or []
                author_name = authors[0].get("family", "") if authors else ""
                if author_name and len(authors) > 1:
                    author_name += " et al."
                elif not author_name:
                    author_name = "Open Access Author"

                summary = f"Open Access PDF via Unpaywall (License: {best_oa.get('license', 'unknown')}, Host: {best_oa.get('host_type', 'repository')})."
                
                out.append(
                    Result(
                        title=f"{title} (OA PDF)",
                        url=pdf_url,
                        summary=summary,
                        source="unpaywall",
                        kind="paper",
                        creator=author_name,
                        creator_url=f"https://doi.org/{doi}",
                    )
                )
        except Exception:
            continue

    return out
