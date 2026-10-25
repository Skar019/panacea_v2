"""Panacea P1 Evaluation Script.
Compares Panacea (planned + model-ranked top 6) vs Baseline (plain keyword
search + round-robin mix top 6) across 20 student projects.
Saves progress after every project in eval_results.json so you can pause
and resume across days without losing work or wasting Gemini quota.

Run in PowerShell: py eval.py"""
import json
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    # Fixes Windows certificate errors
    import truststore
    truststore.inject_into_ssl()
except ImportError:
    pass

from adapters import ADAPTERS
from planner import plan, SOURCES_BY_DOMAIN
from core import search, rank, _mix

SAVE_FILE = "eval_results.json"
TOP_K = 6

PROJECTS = [
    ("hardware", "build a 6-axis robot arm with 3D printed parts"),
    ("hardware", "solar powered automated drip irrigation controller using ESP32"),
    ("hardware", "3D printed prosthetic hand controlled by EMG muscle sensors"),
    ("hardware", "low-cost cansat telemetry payload with LoRa 433MHz"),
    ("hardware", "smart HVAC thermostat controller using ESP32 and infrared transmitter"),
    ("hardware", "autonomous line following mobile robot with PID control"),
    ("hardware", "homemade CNC PCB milling machine using stepper motors"),
    ("research", "corrosion resistance of zinc phosphate conversion coatings on steel"),
    ("research", "bioaccumulation and depletion kinetics of ciprofloxacin in catfish muscle"),
    ("research", "antimicrobial resistance genomic surveillance in West Africa"),
    ("research", "sacrificial anode cathodic protection design for marine steel piles"),
    ("research", "heat retention of brewed bitter leaf Vernonia amygdalina extract"),
    ("research", "microplastic removal efficiency in municipal wastewater treatment plants"),
    ("research", "pharmacokinetic modeling of oral antimalarial artemisinin combination therapy"),
    ("software", "indirect prompt injection benchmark for tool-using LLM agents"),
    ("software", "credit card fraud detection web app in Python with scikit-learn"),
    ("software", "offline Yoruba to English speech translation app for mobile"),
    ("software", "student timetable generator using genetic algorithm in Python"),
    ("software", "molecular property prediction and SMILES visualization using RDKit"),
    ("software", "real-time pothole detection on roads using YOLOv8 and OpenCV"),
]


def load_saved():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"judged": {}}


def save_progress(data):
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def judge_list(label, items, description):
    print(f"\n--- {label} (Top {len(items)}) ---")
    print(f"Goal: {description}")
    if not items:
        print("  (0 results returned — honest silence)")
        return 0, 0
    relevant = 0
    for i, r in enumerate(items, 1):
        print(f"\n  [{i}/{len(items)}] [{r.source}] {r.title}")
        print(f"        URL: {r.url}")
        if getattr(r, "why", ""):
            print(f"        Why: {r.why}")
        if r.summary:
            print(f"        Info: {' '.join(r.summary.split())[:140]}")
        while True:
            ans = input("        Is this genuinely useful for the student? [y/n/q to quit]: ").strip().lower()
            if ans in ("y", "yes"):
                relevant += 1
                break
            if ans in ("n", "no"):
                break
            if ans in ("q", "quit"):
                raise KeyboardInterrupt
    return relevant, len(items)


def print_summary(data):
    judged = data.get("judged", {})
    if not judged:
        print("\nNo projects judged yet.")
        return
    p_rel = sum(v["panacea_rel"] for v in judged.values())
    p_tot = sum(v["panacea_shown"] for v in judged.values())
    b_rel = sum(v["baseline_rel"] for v in judged.values())
    b_tot = sum(v["baseline_shown"] for v in judged.values())

    p_prec = (p_rel / p_tot * 100) if p_tot else 0.0
    b_prec = (b_rel / b_tot * 100) if b_tot else 0.0

    print("\n" + "=" * 60)
    print(f"EVALUATION SUMMARY ({len(judged)}/{len(PROJECTS)} projects judged by human)")
    print("=" * 60)
    print(f"Panacea (AI plan + rank): {p_rel}/{p_tot} relevant ({p_prec:.1f}% precision@{TOP_K})")
    print(f"Plain keyword baseline  : {b_rel}/{b_tot} relevant ({b_prec:.1f}% precision@{TOP_K})")
    print("=" * 60)


def main():
    data = load_saved()
    print(f"Loaded {len(data['judged'])}/{len(PROJECTS)} completed evaluations.")
    print_summary(data)

    try:
        for idx, (expected_domain, desc) in enumerate(PROJECTS, 1):
            if desc in data["judged"]:
                continue

            print(f"\n\n[{idx}/{len(PROJECTS)}] Testing: {desc}")
            cmd = input("Press Enter to run this project, 's' to skip, or 'q' to quit: ").strip().lower()
            if cmd == "q":
                break
            if cmd == "s":
                continue

            domain, queries, sources, wants = plan(desc, list(ADAPTERS))
            found_p, _ = search(queries, sources)
            ranked_p, used_model = rank(desc, found_p, wants=wants)
            if not used_model:
                print("WARNING: Model unavailable (quota reached). Stopping so we only record true model-ranked runs.")
                break
            top_panacea = ranked_p[:TOP_K]

            base_sources = [s for s in SOURCES_BY_DOMAIN.get(expected_domain, list(ADAPTERS)) if s in ADAPTERS]
            found_b, _ = search([desc], base_sources)
            top_baseline = _mix(found_b)[:TOP_K]

            p_rel, p_shown = judge_list("Method A: PANACEA", top_panacea, desc)
            b_rel, b_shown = judge_list("Method B: PLAIN KEYWORD BASELINE", top_baseline, desc)

            data["judged"][desc] = {
                "domain": expected_domain,
                "panacea_rel": p_rel,
                "panacea_shown": p_shown,
                "baseline_rel": b_rel,
                "baseline_shown": b_shown,
            }
            save_progress(data)
            print(f"\nSaved! Panacea: {p_rel}/{p_shown} | Baseline: {b_rel}/{b_shown}")

    except KeyboardInterrupt:
        print("\nPaused and saved progress.")

    print_summary(data)


if __name__ == "__main__":
    main()
