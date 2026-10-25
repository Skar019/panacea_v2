"""Hugging Face Hub adapter (datasets and models, free public API, no key required)."""
import urllib.parse
import net
from .base import Result, register


@register("huggingface")
def search_huggingface(query, limit=5):
    q = urllib.parse.quote(query)
    out = []
    half = max(2, limit // 2)

    # 1. Search HF Datasets
    ds_url = f"https://huggingface.co/api/datasets?search={q}&limit={half}&sort=downloads&direction=-1"
    for d in net.get_json(ds_url) or []:
        repo_id = d.get("id") or ""
        if not repo_id:
            continue
        owner = repo_id.split("/")[0] if "/" in repo_id else ""
        owner_url = f"https://huggingface.co/{owner}" if owner else ""
        desc = (d.get("description") or "").strip()[:300]
        out.append(
            Result(
                f"{repo_id} (Dataset)",
                f"https://huggingface.co/datasets/{repo_id}",
                desc,
                "huggingface",
                "dataset",
                owner,
                owner_url,
            )
        )

    # 2. Search HF Models
    mod_url = f"https://huggingface.co/api/models?search={q}&limit={limit - len(out)}&sort=downloads&direction=-1"
    for m in net.get_json(mod_url) or []:
        repo_id = m.get("id") or ""
        if not repo_id:
            continue
        owner = repo_id.split("/")[0] if "/" in repo_id else ""
        owner_url = f"https://huggingface.co/{owner}" if owner else ""
        pipeline = m.get("pipeline_tag") or "model"
        downloads = m.get("downloads") or 0
        desc = f"Hugging Face {pipeline} ({downloads:,} downloads)."
        out.append(
            Result(
                f"{repo_id} (Model)",
                f"https://huggingface.co/{repo_id}",
                desc,
                "huggingface",
                "model",
                owner,
                owner_url,
            )
        )

    return out[:limit]
