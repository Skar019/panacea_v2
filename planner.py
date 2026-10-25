from llm import ask, extract_json

PROMPT = """A student describes a project they want help with:
"{d}"

Return ONLY JSON like:
{{"domain": "hardware", "wants": ["cad", "videos"], "queries": ["...", "...", "..."]}}

- domain: one of research, software, hardware, other
- wants: the kinds of resource the student explicitly asked for, chosen from:
  papers, code, cad, videos, web. Use [] if they did not say. Only include
  what they actually asked for.
- queries: 3 searches to find prior work.
  - for papers: keyword searches a specialist would use: scientific or
    technical names (e.g. Latin plant names), synonyms, the underlying phenomenon.
  - for anything else: SHORT searches of 2 to 3 words, like terms typed into
    GitHub or YouTube (example: "fraud detection", "6dof robot arm").
  - keep the project's meaning: never leave an ambiguous word alone
    ("robot arm", not "arm").
  Keywords only, no full sentences."""

SOURCES_BY_DOMAIN = {
    "research": ["semantic_scholar", "openalex", "pubmed", "arxiv", "huggingface"],
    "software": ["github", "huggingface", "guides"],
    "hardware": ["github", "openalex", "cad", "guides"],
}

# What the student can ask for -> which sources to use
WANTS_TO_SOURCES = {
    "papers": ["semantic_scholar", "openalex", "pubmed", "arxiv"],
    "code": ["github", "huggingface"],
    "cad": ["cad"],
    "videos": ["guides"],
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
