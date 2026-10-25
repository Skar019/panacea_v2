"""The people step: who made this, and a first message to them.
Only public information the maker chose to publish is used. Panacea never
sends anything: the student reads, edits and sends it themselves."""
import os
import net
from llm import ask


def maker_info(r):
    """Public profile facts from GitHub or OpenAlex author records."""
    if not r.creator:
        return {}

    if r.source == "github":
        try:
            headers = {"Accept": "application/vnd.github+json"}
            if os.environ.get("GITHUB_TOKEN"):
                headers["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]
            data = net.get_json(f"https://api.github.com/users/{r.creator}", headers=headers)
            keys = ("name", "bio", "company", "blog", "email", "twitter_username")
            return {k: data[k] for k in keys if data.get(k)}
        except Exception:
            return {}

    if r.source == "openalex" and r.creator_url:
        try:
            tail = r.creator_url.rstrip("/").split("/")[-1]
            url = f"https://api.openalex.org/authors/{tail}"
            data = net.get_json(url)
            info = {}
            if data.get("display_name"):
                info["name"] = data["display_name"]
            insts = data.get("last_known_institutions") or []
            if insts and insts[0].get("display_name"):
                info["institution"] = insts[0]["display_name"]
            if data.get("works_count") is not None:
                info["publications"] = f"{data['works_count']} indexed works"
            if data.get("cited_by_count") is not None:
                info["citations"] = f"{data['cited_by_count']} citations"
            if data.get("orcid"):
                info["orcid"] = data["orcid"]
            return info
        except Exception:
            return {}

    return {}


PROMPT = """Write a short, polite first message from a student to the maker of
something they found online.
Student's goal: {goal}
What they found: "{title}" by {who} ({url}). It says: {about}

Rules:
- under 90 words, plain friendly English, no flattery cliches
- say what the student is building and what exactly they found useful
- ask ONE specific question; if you cannot tell what to ask, write [your specific question]
- do not invent facts about the maker or the work
- start with "Hello" and the name (first name if clear), end with "Thank you, [Your name]"
Return only the message."""


def draft_message(goal, r):
    about = " ".join((r.summary or "").split())[:200] or "(no description)"
    msg = ask(PROMPT.format(
        goal=goal,
        title=r.title,
        who=r.creator or "the author",
        url=r.url,
        about=about,
    ))
    if msg and msg.strip():
        return msg.strip()
    name = (r.creator or "there").split("(")[0].replace(" et al.", "").strip()
    return (
        f"Hello {name},\n\n"
        f"I'm a student working on: {goal}. I found \"{r.title}\" ({r.url}) "
        f"and it has been very useful for my project. "
        f"Could I ask you one question: [your specific question]?\n\n"
        f"Thank you for sharing your work openly.\n[Your name]"
    )
