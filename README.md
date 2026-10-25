# Panacea

**Panacea** is a domain-agnostic web app for students starting a research, software, or hardware project. A student describes what they want to build or investigate in plain language; Panacea returns the top ~6 starting resources (papers, code repositories, ML datasets/models, 3D CAD files, and build tutorials), explains why each result helps, shows public information about who created it, and drafts a polite, editable first message to reach out to them.

## Why We Built This (The Problem)

Students starting a final-year undergraduate project, a hardware build, or a literature review often do not know what prior work exists or how to approach someone experienced:

* **Stretched Academic Supervision:** Nigeria's National Universities Commission (NUC) reported roughly **100,000 academic staff for 2.1 million university students**—an average ratio of about **1:21** (reported by *Nigerian Tribune*, Jan 2022, and *The Guardian Nigeria*, 2024, citing the NUC bulletin; NUC benchmarks range from 1:15 to 1:30 by field). An older study of 9 of 27 Nigerian federal universities also links higher student-to-supervisor ratios to weaker final-year project supervision.
* **Paywalled Literature:** A study of African emergency-care publications found a mean single-article access cost of **$36.44**.
* **Cold-Messaging Friction:** Even when students find a relevant paper, repository, or CAD model, many hesitate to contact the creator because they do not know what to ask.

## Measured Evaluation Results

We evaluated Panacea against a plain keyword search baseline (using the student's raw project description across the same domain sources, interleaved round-robin) across **12 student projects** spanning hardware, software, and scientific research. A human judge scored each of the top 6 results returned by each method as relevant or not:

| Method | Projects Judged | Relevant / Total Shown (Top 6) | Precision@6 |
| :--- | :---: | :---: | :---: |
| **Panacea (AI query planning + strict ranking)** | 12 | **54 / 72** | **75.0%** |
| **Plain keyword search baseline (no LLM)** | 12 | 40 / 71 | 56.3% |

* **Result:** Panacea improved top-6 precision by **+18.7 percentage points** (75.0% vs 56.3%) over plain keyword search.
* **Unit Tests:** 3 offline mock-based unit tests (`py test_panacea.py`) covering planner JSON parsing, ranker reason extraction, and OpenAlex author profile lookup (`Ran 3 tests in 0.002s — OK`).

## How It Works

1. **Planner (planner.py)**: Uses one LLM call to classify the project domain (research, software, hardware, other) and generate 3 tailored searches—specialist scientific/Latin terms for papers, and short 2–3 word queries for GitHub, Hugging Face, CAD sites, and tutorials.
2. **Multi-Source Search (core.py, adapters/)**: Queries OpenAlex, Semantic Scholar, PubMed, arXiv, GitHub, Hugging Face (datasets & models), CAD repositories (GrabCAD, Printables, Thingiverse, MakerWorld, Cults3D via Tavily), and build guides (YouTube, Instructables, Hackaday via Tavily). A failure in one source never blocks the rest.
3. **Strict Ranker (core.py)**: Interleaves up to 30 candidates across sources and uses one LLM call to pick the best matches, filter out word-sense collisions, and attach a 1-sentence "Why this result" explanation—or return honest silence ([]) when nothing relevant exists.
4. **Public Maker Info & Outreach Draft (people.py)**: Uses public profile APIs only (GitHub user profiles and OpenAlex author records) and drafts a <90-word message with one specific question placeholder. Panacea never sends messages automatically.
5. **Free-Tier Quota Protection (app.py, llm.py)**: Caches model-ranked searches across sessions, rotates across free-tier models on HTTP 429/403/404, limits shared-key usage to 5 uncached searches per session, and lets visitors enter their own free Gemini API key in the sidebar (stored only in browser session state).

## Run Locally (Windows PowerShell)

    py -m pip install streamlit python-dotenv truststore
    copy .env.example .env
    # Add your NEBIUS_API_KEY (Gemini key) and TAVILY_API_KEY to .env
    py -m streamlit run app.py

* **CLI mode:** `py main.py`
* **Offline unit tests:** `py test_panacea.py`
* **Evaluation benchmark:** `py eval.py`

## License
MIT
