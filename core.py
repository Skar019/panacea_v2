"""Search orchestration, strict relevance scoring (0-10), and 2-stage retry loop."""
from adapters import ADAPTERS
from llm import ask, extract_json

RANK_PROMPT = """A student describes a project they want help with:
"{d}"
{wants_note}

Below are candidate resources found across multiple databases:
{items}

Your task is to act as a strict senior engineering/research mentor filtering these candidates.
Score each relevant item from 0 to 10 based on how directly it helps this exact project:
- 9-10: Direct match (same mechanism, organism/compound, architecture, or hardware assembly).
- 8: Strong reusable component, methodology, or dataset directly applicable to the project.
- 0-7: Tangential, wrong word-sense (e.g. biological "arm" vs "robot arm"), generic textbook fluff, or off-topic. DO NOT include anything scoring below 8.

It is much better to return 2 or 3 dead-on hits (score >= 8) than to pad the list with mediocre matches. If nothing scores >= 8, return [].

Return ONLY a JSON list of objects (best first, up to {k} items) like:
[{{"id": 0, "score": 9, "why": "One specific sentence explaining exactly how this resource helps their project."}}]"""

WANTS_LABELS = {
    "papers": "research papers or open-access PDFs",
    "code": "code repositories, models, or datasets",
    "cad": "3D / CAD model files",
    "videos": "video tutorials or step-by-step build guides",
    "social": "developer/maker posts from X, TikTok, Instagram, or Reddit",
    "web": "web pages",
}


def search(queries, sources, per_query=5):
    """Run queries across sources, deduplicate by URL, and interleave round-robin
    so no single source drowns out the others."""
    by_source = {s: [] for s in sources if s in ADAPTERS}
    errors = {}
    seen = set()

    for s in by_source:
        fn = ADAPTERS[s]
        for q in queries:
            try:
                for r in fn(q, limit=per_query):
                    if r.url and r.url not in seen:
                        seen.add(r.url)
                        by_source[s].append(r)
            except Exception as e:
                errors[s] = str(e)

    # Interleave round-robin across sources
    mixed = []
    buckets = [lst for lst in by_source.values() if lst]
    i = 0
    while buckets:
        nxt = []
        for b in buckets:
            if i < len(b):
                mixed.append(b[i])
                if i + 1 < len(b):
                    nxt.append(b)
        buckets = nxt
        i += 1
    return mixed, errors


def rank(description, results, top_k=12, wants=None):
    """Rank up to 35 candidates with full 320-char summaries and a strict >= 8/10 filter.
    Returns (ranked_list, used_model_bool)."""
    if not results:
        return [], True

    pool = results[:35]
    lines = []
    for idx, r in enumerate(pool):
        summary_clean = " ".join((r.summary or "").split())[:320]
        creator_str = f" | Creator: {r.creator}" if getattr(r, "creator", "") else ""
        lines.append(
            f"[{idx}] ({r.source} / {r.kind}{creator_str}) {r.title} — {summary_clean}"
        )

    wants_note = ""
    if wants:
        wanted_names = [WANTS_LABELS.get(w, w) for w in wants]
        wants_note = (
            "IMPORTANT: The student specifically asked for: "
            + ", ".join(wanted_names)
            + ". Prioritize those resource types heavily."
        )

    prompt = RANK_PROMPT.format(
        d=description,
        wants_note=wants_note,
        items="\n".join(lines),
        k=top_k,
    )
    reply = extract_json(ask(prompt))
    if isinstance(reply, list):
        out = []
        seen_ids = set()
        for item in reply:
            if isinstance(item, dict) and isinstance(item.get("id"), int):
                idx = item["id"]
                score = item.get("score", 8)
                try:
                    score_val = float(score)
                except (ValueError, TypeError):
                    score_val = 8.0
                if 0 <= idx < len(pool) and idx not in seen_ids and score_val >= 8:
                    seen_ids.add(idx)
                    r = pool[idx]
                    r.why = (item.get("why") or "").strip()
                    r.score = int(round(score_val))
                    out.append(r)
            elif isinstance(item, int):
                idx = item
                if 0 <= idx < len(pool) and idx not in seen_ids:
                    seen_ids.add(idx)
                    out.append(pool[idx])
        return out[:top_k], True

    # Fallback if the LLM is unreachable
    return pool[:top_k], False
