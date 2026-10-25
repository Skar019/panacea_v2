try:                                  # fixes Windows certificate errors
    import truststore
    truststore.inject_into_ssl()
except ImportError:
    pass

from dotenv import load_dotenv
load_dotenv()

from adapters import ADAPTERS
from planner import plan, clarify
from core import search, rank

BATCH = 6          # how many results to show at a time

def show(items, start):
    for n, r in enumerate(items, start + 1):
        print(f"{n}. [{r.source}] {r.title}\n   {r.url}")
        text = " ".join(r.summary.replace("#", " ").split())
        if "copyright" in text.lower() or "treaties" in text.lower():
            text = ""          # skip legal boilerplate
        if text:
            print(f"   {text[:140]}")
            
def run_search(description):
    domain, queries, sources, wants = plan(description, list(ADAPTERS))
    kinds = f" (you asked for: {', '.join(wants)})" if wants else ""
    print(f"\nType: {domain}{kinds}\nSearching {', '.join(sources)} for: {queries}\n")
    results, errors = search(queries, sources)
    ranked, used_model = rank(description, results, wants)
    return domain, ranked, len(results), errors, used_model

if __name__ == "__main__":
    description = input("Describe your project (you can also say what you want, "
                        "e.g. 'only CAD files'): ")
    question = clarify(description)
    if question:
        extra = input(f"\n{question}\n(type more detail, or press Enter to skip)\n> ")
        if extra.strip():
            description += ". " + extra.strip()

    while True:
        domain, ranked, found, errors, used_model = run_search(description)
        shown = min(BATCH, len(ranked))
        if ranked:
            show(ranked[:shown], 0)
            note = "" if used_model else " (model unavailable, so these are unranked)"
            print(f"\nShowing {shown} of {len(ranked)} best matches ({found} found){note}.")
        elif found:
            print(f"Nothing looked relevant ({found} found). Try describing it differently.")
        elif domain in ("research", "unknown"):
            print("No matches at all. That may mean the topic is under-studied.")
        else:
            print("No matches at all. Try describing it with simpler words.")
        for name, err in errors.items():
            print(f"{name} unavailable: {err}")

        refine = None
        while refine is None:
            more = shown < len(ranked)
            prompt = ("\n[m] see more, or type what else you want (e.g. 'only videos'), "
                      "Enter to finish\n> " if more else
                      "\nNo more strong matches. Type what else you want, "
                      "or Enter to finish\n> ")
            reply = input(prompt).strip()
            if not reply:
                raise SystemExit
            if reply.lower() in ("m", "more"):
                if more:
                    show(ranked[shown:shown + BATCH], shown)
                    shown = min(shown + BATCH, len(ranked))
                    print(f"\nShowing {shown} of {len(ranked)} best matches.")
                else:
                    print("That's everything strong I found.")
            else:
                refine = reply
        description += ". " + refine
