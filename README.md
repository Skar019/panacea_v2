# Panacea

**Describe any project, in any field. Panacea finds what a mentor would point you to:
papers, code, CAD files, tutorials, and the people who made them.**

Many students have no easy way to ask someone experienced "where do I even start?".
Panacea does the first round of that digging: it searches across sources, keeps only the
best few results, and, where the material itself isn't enough, shows who made it and
drafts a polite first message you can edit and send yourself.

## What it does

1. **Understands the project.** One model call works out what kind of project it is
   (research, software, hardware, other) and rewrites your description into the short
   searches a specialist would use (for example, Latin plant names for a plant-science topic).
2. **Searches the right sources.** Papers: Semantic Scholar, OpenAlex, PubMed, arXiv.
   Code: GitHub. CAD files: GrabCAD, Printables, Thingiverse, MakerWorld, Cults3D.
   Tutorials: YouTube, Instructables, Hackaday. Open web: via Tavily.
3. **Keeps the best 6, with "See more".** A second model call ranks everything found and
   skips off-topic results. If nothing is relevant, it says so instead of padding the list.
4. **You choose the kind of help.** Pick papers, code, CAD files, videos or web pages, or
   leave it empty and the model decides.
5. **Reach out to the maker.** Shows the creator's public profile and drafts a short first
   message. Panacea never sends anything.

## Limits, stated plainly

- It finds and ranks resources. It does not write your project for you.
- The people step uses only information the maker chose to make public. It does not scrape
  emails or social media.
- Results depend on the model and on free-tier limits of the services it calls. When the
  model is unavailable it falls back to a plain mix of results and says so on the page.
- Maker detection from titles and channel text is best-effort; some results show no maker.

## Run it yourself

```
py -m pip install -r requirements.txt
copy .env.example .env      # then fill in your keys
py -m streamlit run app.py
```

The command-line version is `py main.py`.

## Settings (`.env` locally, "Secrets" when hosted)

See `.env.example`. Panacea works with any OpenAI-compatible model service, so switching
provider means changing three values, not code.

## How it is built

Python, Streamlit, and plain standard-library HTTP calls. Each source is one small
function in `adapters/`; adding a source means adding one file and one import line.
`planner.py` decides what to search, `core.py` searches and ranks, `people.py` handles the
maker step, `app.py` is the web page.

## Built with AI assistance

The code was written with help from Claude (Anthropic) and reviewed and tested by the author.

## License

MIT. See `LICENSE`.
