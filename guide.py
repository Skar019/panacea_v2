"""Interactive project mentorship ("Guide me with this") tailored to resource kind:
- Research papers: paper/thesis structure, field lingo translation, and experimental blueprint.
- CAD / Hardware: file format tips (.STEP vs .STL), SolidWorks/CAD modifications, and engineering calculations for new loads/use-cases.
- Code / Tutorials / Social: architecture breakdown, key files/components, and step-by-step adaptation."""
from llm import ask

PAPER_PROMPT = """You are a patient senior academic research mentor helping an undergraduate or early-stage researcher.
The student is working on this project:
"{base_project}"

Their specific experiment, research question, or writing goal is:
"{user_goal}"

They selected this reference paper to guide them:
- Title: {title}
- Source: {source}
- Summary / Abstract: {summary}

Write a clear, structured mentorship guide (NOT a template to copy-paste, but an interactive breakdown that teaches them how to write and execute their own work using this paper as a blueprint):

1. **Decoding the Field's Lingo (Plain-English Glossary)**:
   Identify 4 to 5 technical terms, assay names, statistical metrics, or domain phrases from this paper's title/abstract and explain what they actually mean in plain English and why researchers use them.

2. **How a Paper / Thesis in This Field is Structured**:
   Show how each section of their paper/thesis should be built around their topic ("{user_goal}"):
   - **Title & Abstract**: How to state the organism/system, variable tested, quantitative metric, and key takeaway.
   - **Introduction (The Funnel)**: How to move from the broad real-world problem -> what prior studies (like "{title}") did -> the specific gap their project fills -> their objective.
   - **Materials & Methods**: What experimental controls, standards/protocols, sample sizes, or analytical equations they need to specify so another scientist could reproduce it.
   - **Results vs. Discussion**: Explain the difference between reporting raw data/trends (Results) and comparing their findings against prior literature like this paper (Discussion).

3. **How to Use This Specific Paper Without Copying It**:
   Give 3 concrete ways they can use "{title}" as a benchmark (e.g. borrowing the methodology/exposure schedule, using its findings as a baseline comparison, or citing it to justify a parameter choice) while keeping their own work original."""

CAD_PROMPT = """You are a senior mechanical & hardware design mentor.
The student's overall project is:
"{base_project}"

They selected this CAD / hardware reference:
- Title: {title}
- Source: {source}
- Description: {summary}

The student's CAD software / fabrication tools:
"{user_tools}"

The student's specific use case, load, or modification compared to the original model:
"{user_mod}"

Write a practical, first-principles engineering modification guide tailored to their tools and use case:

1. **CAD File Format & Import Strategy ({user_tools})**:
   Explain what file formats to look for on the download page (e.g. parametric `.SLDPRT`/`.SLDASM`, neutral solid `.STEP`/`.IGES` vs mesh `.STL`/`.3MF`), how to inspect or rebuild key features in **{user_tools}**, and what reference planes/mates to establish first.

2. **What Changes for Your Use Case ("{user_mod}")**:
   Compare the original model's likely operating conditions with the student's new use case. Break down the physics and mechanical design changes required:
   - **Loads, Stresses & Kinematics**: Which forces/torques change (e.g. axial vs radial load, bending moment, friction, self-locking condition, buckling, or gear ratio) and which back-of-the-envelope equations to check first.
   - **Geometry & Tolerances**: Which dimensions (wall thickness, shaft/bore clearances, thread pitch/lead, fillets, mounting holes) must be resized in **{user_tools}**.
   - **Material & Manufacturing Choice**: What material or off-the-shelf hardware (bearings, fasteners, lead screws, motors) should be used instead of purely 3D-printed plastic where high stress occurs.

3. **Step-by-Step Modification Checklist**:
   Give a numbered, 4-step workflow to take this reference model, modify it safely in **{user_tools}**, and verify it before fabrication."""

CODE_PROMPT = """You are a senior software and systems engineering mentor.
The student's project is:
"{base_project}"

They selected this reference resource ({kind} from {source}):
- Title: {title}
- URL: {url}
- Summary: {summary}

The student's tech stack / environment:
"{user_tools}"

What the student wants to adapt or build using this resource:
"{user_mod}"

Write a clear, practical implementation and adaptation guide:

1. **How This Resource Fits Together (Architecture & Key Concepts)**:
   Break down what "{title}" does under the hood, the core concepts/libraries it relies on, and which parts of a repository/post like this actually matter for their goal.

2. **What to Keep vs. What to Modify for "{user_mod}"**:
   - **Keep / Reuse Directly**: Which data pipelines, model weights, helper functions, or hardware wiring patterns they should reuse as-is.
   - **Modify / Swap Out**: What exact changes are needed to make it work with **{user_tools}** and their custom use case ("{user_mod}").

3. **Step-by-Step Execution Plan**:
   Give a numbered, 4-step action plan to clone/test the baseline first, make one isolated modification at a time, and validate that it works."""


def generate_guide(base_project, r, user_tools="", user_mod=""):
    """Generate a tailored mentorship guide for Result `r`."""
    base = (base_project or r.title or "Student project").strip()
    title = (r.title or "Untitled resource").strip()
    summary = (r.summary or "No summary provided.").strip()

    if r.kind == "paper":
        goal = (user_mod or base).strip()
        prompt = PAPER_PROMPT.format(
            base_project=base,
            user_goal=goal,
            title=title,
            source=r.source,
            summary=summary,
        )
    elif r.kind == "cad-files" or r.source == "cad":
        tools = (user_tools or "SolidWorks / standard CAD").strip()
        mod = (user_mod or f"Adapting this model for: {base}").strip()
        prompt = CAD_PROMPT.format(
            base_project=base,
            title=title,
            source=r.source,
            summary=summary,
            user_tools=tools,
            user_mod=mod,
        )
    else:
        tools = (user_tools or "Python / standard dev environment").strip()
        mod = (user_mod or f"Adapting this resource for: {base}").strip()
        prompt = CODE_PROMPT.format(
            base_project=base,
            kind=r.kind,
            source=r.source,
            title=title,
            url=r.url,
            summary=summary,
            user_tools=tools,
            user_mod=mod,
        )

    reply = ask(prompt)
    if reply and reply.strip():
        return reply.strip()

    return (
        "*(The AI mentor is temporarily unavailable due to API rate limits. "
        "Wait a moment or add your personal free Gemini API key in the left sidebar and click **Generate Guide** again.)*"
    )
