from llm import ask, extract_json

PROMPT = """A student describes a project they want help with:
"{d}"

Return ONLY JSON like:
{{"domain": "hardware", "wants": ["cad", "videos"], "queries": ["...", "...", "..."]}}

- domain: one of research, software, hardware, other
- wants: the kinds of resource the student explicitly asked for, chosen from:
  papers, code, cad, videos, social, web. Use [] if they did not say. Only include
  what they actually asked for (use "social" if they mention Twitter, X, TikTok, Instagram, Reddit, or social media).
- queries: 3 searches to find prior work.
  - for papers: keyword searches a specialist would use: scientific or
    technical names (e.g. Latin species names, chemical/pharmacological terms), synonyms, and the underlying mechanism.
  - for anything else: SHORT searches of 2 to 4 words, like terms typed into
    GitHub, GrabCAD, X/Twitter, or YouTube (example: "fraud detection", "6dof robot arm", "power screw jack").
  - keep the project's meaning: never leave an ambiguous word alone
    ("robot arm", not "arm").
  Keywords only, no full sentences."""

RETRY_PROMPT = """A student describes a project:
"{d}"

We already tried these search queries: {old_queries}
Those searches returned too few direct matches (or off-topic results).
 Sample titles that came back: {sample_titles}

Generate 3 NEW, sharper search queries that take a different angle:
- If the previous queries were too broad or ambiguous, add the specific domain noun (e.g. "mechanical", "Arduino", "Python", "bioaccumulation", "finite element").
- If the previous queries were too long or narrow, use standard 2-3 word engineering/scientific terms.
Return ONLY JSON like:
{{"queries": ["...", "...", "..."]}}"""

SOURCES_BY_DOMAIN = {
    "research": ["semantic_scholar", "openalex", "pubmed", "arxiv", "huggingface", "unpaywall"],
    "software": ["github", "huggingface", "guides", "social"],
    "hardware": ["github", "openalex", "cad", "guides", "social"],
}

# What the student can ask for -> which sources to use
WANTS_TO_SOURCES = {
    "papers": ["semantic_scholar", "openalex", "pubmed", "arxiv", "unpaywall"],
    "code": ["github", "huggingface"],
    "cad": ["cad"],
    "videos": ["guides"],
    "social": ["social"],
    "web": ["web"],
}


def plan(description, all_sources):
    """Returns (domain, queries, sources, wants)."""
    reply = extract_json(ask(PROMPT.format(d=description)))
    if isinstance(reply, dict) and reply.get("queries"):
        domain = reply.get("domain", "other")
        queries = [q.strip() for q in reply["queries"] if isinstance(q, str) and q.strip()][:3]
        wants = [w for w in (reply.get("wants") or []) if w in WANTS_TO_SOURCES]
        if wants:
            # The student chose the resource types
            sources = []
            for w in wants:
                for s in WANTS_TO_SOURCES[w]:
                    if s in all_sources and s not in sources:
                        sources.append(s)
        else:
            # The model decides
            chosen = SOURCES_BY_DOMAIN.get(domain, all_sources)
            sources = [s for s in chosen if s in all_sources]
        if queries:
            return domain, queries, sources or list(all_sources), wants
    return "unknown", [description], list(all_sources), []  # no-model fallback


def replan(description, old_queries, found_results):
    """Generate up to 3 alternative search queries when the first pass yields weak matches."""
    sample_titles = [r.title for r in (found_results or [])[:6] if getattr(r, "title", "")]
    prompt = RETRY_PROMPT.format(
        d=description,
        old_queries=", ".join(old_queries),
        sample_titles="; ".join(sample_titles) if sample_titles else "None found",
    )
    reply = extract_json(ask(prompt))
    if isinstance(reply, dict) and isinstance(reply.get("queries"), list):
        old_set = {q.lower().strip() for q in old_queries}
        new_q = [
            q.strip()
            for q in reply["queries"]
            if isinstance(q, str) and q.strip() and q.lower().strip() not in old_set
        ]
        return new_q[:3]
    return []


CLARIFY_PROMPT = """A student describes a project: "{d}"
Is this specific enough to search for prior work, or is it ambiguous (a word with
more than one meaning, or the goal is unclear)? If it is clear, reply exactly: OK
Otherwise reply with ONE short question that would settle the ambiguity.
Reply with only OK or the question."""


def clarify(description):
    """Return a follow-up question, or None if no more detail is needed."""
    if len(description.split()) >= 8:
        return None  # detailed enough: save a model call
    reply = ask(CLARIFY_PROMPT.format(d=description))
    if reply is None:
        return "Add more detail: what exactly do you want to find out or build?"
    reply = reply.strip()
    return None if reply.upper().startswith("OK") else reply
