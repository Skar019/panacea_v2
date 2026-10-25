"""Panacea web page. Run locally: py -m streamlit run app.py"""
import os
import re
import streamlit as st

for _k in (
    "NEBIUS_API_KEY",
    "NEBIUS_BASE_URL",
    "NEBIUS_MODELS",
    "NEBIUS_MODEL",
    "TAVILY_API_KEY",
    "GITHUB_TOKEN",
    "S2_API_KEY",
    "OPENALEX_EMAIL",
    "UNPAYWALL_EMAIL",
):
    try:
        if _k in st.secrets and _k not in os.environ:
            os.environ[_k] = str(st.secrets[_k])
    except Exception:
        pass

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    import truststore
    truststore.inject_into_ssl()
except ImportError:
    pass

from adapters import ADAPTERS
from planner import plan, clarify, WANTS_TO_SOURCES
from core import search, rank
from people import maker_info, draft_message

PAGE = 6
MAX_FREE_SEARCHES = 5

TYPES = {
    "Papers": "papers",
    "Code": "code",
    "CAD files": "cad",
    "Videos & tutorials": "videos",
    "Web pages": "web",
}

LABELS = {
    "github": "Code",
    "huggingface": "Dataset / Model",
    "arxiv": "Paper",
    "semantic_scholar": "Paper",
    "openalex": "Paper",
    "pubmed": "Paper",
    "unpaywall": "Open Access PDF",
    "cad": "CAD files",
    "guides": "Tutorial",
    "web": "Web",
}

st.set_page_config(page_title="Panacea", page_icon="🧭")


@st.cache_resource
def _cache():
    return {}


def _cache_key(description, ui_wants):
    return (description.strip().lower(), tuple(sorted(ui_wants)))


def run(description, ui_wants):
    key = _cache_key(description, ui_wants)
    cache = _cache()
    if key in cache:
        return cache[key], True

    domain, queries, sources, model_wants = plan(description, list(ADAPTERS))
    wants = list(ui_wants) or model_wants
    if ui_wants:
        sources = []
        for w in ui_wants:
            for s in WANTS_TO_SOURCES.get(w, []):
                if s in ADAPTERS and s not in sources:
                    sources.append(s)

    found, errors = search(queries, sources)
    ranked, used_model = rank(description, found, wants=wants)
    out = dict(
        domain=domain,
        queries=queries,
        sources=sources,
        ranked=ranked,
        found=len(found),
        errors=errors,
        used_model=used_model,
    )
    if used_model:
        cache[key] = out
    return out, False


def clean_title(title):
    t = re.sub(r"https?://\S+", "", title or "")
    t = re.sub(r"\s*-\s*Download free.*$", "", t, flags=re.I)
    t = re.sub(
        r"\s*[|\-\u2013]\s*(Thingiverse|Printables\.com|MakerWorld|GrabCAD|Cults3D|YouTube)\s*$",
        "",
        t,
        flags=re.I,
    )
    return " ".join(t.split()) or (title or "Untitled")


def blurb(summary):
    text = " ".join((summary or "").split())
    low = text.lower()
    if (
        "copyright" in low
        or "treaties" in low
        or text.startswith("[")
        or low.startswith("tags")
    ):
        return ""
    return text[:260]


def reach_out(r):
    info = maker_info(r)
    if info:
        src_title = "Public GitHub profile" if r.source == "github" else "Public author record (OpenAlex)"
        st.markdown(f"**{src_title}**")
        for k, v in info.items():
            st.caption(f"{k}: {v}")
    elif r.creator_url:
        st.caption(f"Public profile link: {r.creator_url}")

    if r.kind == "paper":
        st.caption("The paper's page usually lists a corresponding author's email.")

    drafts = st.session_state.setdefault("drafts", {})
    if r.url not in drafts:
        with st.spinner("Drafting a message..."):
            drafts[r.url] = draft_message(st.session_state.get("base", ""), r)

    st.text_area(
        "Draft message (edit it, add your name, send it yourself)",
        value=drafts[r.url],
        height=190,
        key="msg_" + r.url,
    )
    st.caption("Only information the maker chose to make public is used.")


def card(r):
    with st.container(border=True):
        label = LABELS.get(r.source, r.source)
        title = clean_title(r.title).replace("[", "(").replace("]", ")")
        st.markdown(f"**[{title}]({r.url})** · `{label}`")
        if getattr(r, "why", ""):
            st.caption(f"Why this result: {r.why}")
        b = blurb(r.summary)
        if b:
            st.write(b)
        if r.creator:
            who = f"[{r.creator}]({r.creator_url})" if r.creator_url else r.creator
            st.caption(f"By {who}")
            if st.button("Reach out to the maker", key="reach_" + r.url):
                st.session_state["reach"] = (
                    None if st.session_state.get("reach") == r.url else r.url
                )
            if st.session_state.get("reach") == r.url:
                reach_out(r)


def execute_search(description, ui_wants):
    used = st.session_state.get("searches_used", 0)
    has_own_key = bool((st.session_state.get("user_api_key") or "").strip())
    is_cached = _cache_key(description, ui_wants) in _cache()

    if not has_own_key and not is_cached and used >= MAX_FREE_SEARCHES:
        st.warning(
            f"You have used all {MAX_FREE_SEARCHES} free searches for this session. "
            "Paste your own free Gemini API key in the sidebar (left) to keep searching."
        )
        return

    with st.spinner("Searching..."):
        res, from_cache = run(description, ui_wants)

    if not has_own_key and not from_cache:
        st.session_state["searches_used"] = used + 1

    st.session_state["result"] = res
    st.session_state["shown"] = PAGE
    st.session_state["base"] = description
    st.session_state["ui_wants"] = ui_wants
    st.session_state["reach"] = None
    st.session_state["clarify_q"] = None
    st.session_state["pending_desc"] = None


with st.sidebar:
    st.subheader("Quota & API Key")
    used_count = st.session_state.get("searches_used", 0)
    remaining = max(0, MAX_FREE_SEARCHES - used_count)
    st.caption(
        f"Free shared-quota searches left this session: **{remaining} / {MAX_FREE_SEARCHES}**"
    )
    st.text_input(
        "Use your own free Gemini key (optional)",
        type="password",
        key="user_api_key",
        help="Get a free key at aistudio.google.com. Stored only in your browser session, never on disk.",
    )
    if (st.session_state.get("user_api_key") or "").strip():
        st.success("Using your personal key (unlimited session searches).")

st.title("🧭 Panacea")
st.write(
    "Describe any project, in any field. Panacea finds what a mentor "
    "would point you to: papers, code, CAD files, datasets and tutorials."
)

desc = st.text_area(
    "What are you working on?",
    height=110,
    placeholder="e.g. build a 6-axis robot arm with 3D printed parts",
)
picked = st.multiselect(
    "What kind of help do you want? (leave empty and Panacea decides)",
    list(TYPES),
)
wants_tuple = tuple(TYPES[p] for p in picked)

if st.button("Find resources", type="primary") and desc.strip():
    clean_desc = desc.strip()
    if len(clean_desc.split()) < 8 and _cache_key(clean_desc, wants_tuple) not in _cache():
        with st.spinner("Checking description..."):
            q = clarify(clean_desc)
        if q:
            st.session_state["clarify_q"] = q
            st.session_state["pending_desc"] = clean_desc
            st.session_state["pending_wants"] = wants_tuple
        else:
            execute_search(clean_desc, wants_tuple)
    else:
        execute_search(clean_desc, wants_tuple)

if st.session_state.get("clarify_q"):
    with st.container(border=True):
        st.markdown(f"**Quick question to narrow this down:** {st.session_state['clarify_q']}")
        extra = st.text_input(
            "Add a bit more detail",
            key="clarify_input",
            placeholder="e.g. for a 3D-printed desktop arm using stepper motors",
        )
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Search with detail", type="primary"):
                combined = f"{st.session_state['pending_desc']} ({extra.strip()})" if extra.strip() else st.session_state["pending_desc"]
                execute_search(combined, st.session_state.get("pending_wants", wants_tuple))
                st.rerun()
        with col2:
            if st.button("Skip & search anyway"):
                execute_search(
                    st.session_state["pending_desc"],
                    st.session_state.get("pending_wants", wants_tuple),
                )
                st.rerun()

res = st.session_state.get("result")
if res:
    ranked = res["ranked"]
    shown = st.session_state.get("shown", PAGE)
    src_list = ", ".join(res["sources"])
    st.caption(
        f"{res['domain']} project · searched {len(res['sources'])} sources ({src_list}) · "
        f"found {res['found']}, kept {len(ranked)}"
    )

    if not res["used_model"]:
        st.info(
            "The AI ranking was unavailable (usage limit), so these results "
            "are a plain mix. Try again in a minute for better ordering."
        )

    if not ranked:
        st.write(
            "Nothing relevant turned up. Try different words, or that may "
            "mean the topic is under-studied."
        )

    for r in ranked[:shown]:
        card(r)

    if ranked:
        st.caption(
            f"Showing {min(shown, len(ranked))} of {len(ranked)} best "
            f"matches ({res['found']} found)."
        )
        if shown < len(ranked) and st.button("See more"):
            st.session_state["shown"] = shown + PAGE
            st.rerun()

    for s, err in res["errors"].items():
        st.caption(f"({s} unavailable: {err})")

    more = st.text_input(
        "Not quite right? Say what else you want",
        placeholder="e.g. only videos, or: for beginners",
    )
    if st.button("Refine") and more.strip():
        refined = f"{st.session_state.get('base', desc)} ({more.strip()})"
        execute_search(refined, tuple())
        st.rerun()