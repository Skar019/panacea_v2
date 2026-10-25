from adapters import ADAPTERS
from llm import ask, extract_json


def search(queries, sources):
    """Every query on every source; a failing source never breaks the rest."""
    out, seen, errors = [], set(), {}
    for q in queries:
        for s in sources:
            try:
                for r in ADAPTERS[s](q):
                    key = r.title.strip().lower()
                    if key and key not in seen:
                        seen.add(key)
                        out.append(r)
            except Exception as e:
                errors[s] = str(e)
    return out, errors


def _mix(results):
    """No-model fallback: take one from each source in turn, so one source
    can't crowd out the others."""
    by_source = {}
    for r in results:
        by_source.setdefault(r.source, []).append(r)
    mixed = []
    while any(by_source.values()):
        for s in list(by_source):
            if by_source[s]:
                mixed.append(by_source[s].pop(0))
    return mixed


def rank(description, results, wants=None, limit=20):
    """Best results first (at most limit). Returns (ranked, used_model)."""
    if not results:
        return [], True
    # Keep the model's job small: at most 30 candidates, mixed across sources
    # so every kind of result is still represented.
    candidates = _mix(results)[:30]
    lines = "\n".join(
        f"{i}. [{r.source}] {r.title} — {' '.join((r.summary or '').split())[:160]}"
        for i, r in enumerate(candidates)
    )
    want_line = ", ".join(wants) if wants else "not specified, so choose the most useful mix"
    prompt = (
        f'A student wants help with: "{description}"\n'
        f"Resource types they asked for: {want_line}\n"
        f"Below are search results. Pick the BEST ones, most useful first, at most {limit}.\n"
        "Be strict: skip anything off-topic, including words used in another sense.\n"
        "If no types were specified, mix source types so the student sees papers, "
        "code, files and tutorials wherever each is genuinely useful.\n"
        "Prefer real projects, tutorials and files over generic pages or collections.\n\n"
        'Return ONLY a JSON list of objects like [{"id": 0, "why": "short 1-sentence reason why this helps"}, ...] '
        "best first, or [] if none are relevant."
    )
    raw = ask(prompt)
    picked = extract_json(raw)
    if isinstance(picked, list):
        out, seen = [], set()
        for item in picked:
            if isinstance(item, dict):
                idx = item.get("id", item.get("index"))
                why = str(item.get("why") or "").strip()
            else:
                idx = item
                why = ""
            if isinstance(idx, int) and 0 <= idx < len(candidates) and idx not in seen:
                seen.add(idx)
                r = candidates[idx]
                r.why = why
                out.append(r)
        return out[:limit], True
    if raw is not None:
        print("(ranking reply was not usable:", repr(raw[:80]), ")")
    return candidates[:limit], False
