"""One small LLM helper. Works with any OpenAI-compatible service.
Defaults to Nebius Token Factory (legacy default). Settings in .env:
  NEBIUS_API_KEY   your key (currently a Gemini key)
  NEBIUS_BASE_URL  the service address
  NEBIUS_MODELS    one or more model ids, comma-separated. If a model hits its
                   daily limit (or isn't available), the next one is tried.
If a visitor enters their own Gemini key in the Streamlit sidebar, their
session key is used instead of the shared key.
If there is no key or every model fails, ask() returns None and Panacea
falls back to plain search."""
import json
import os
import re
import time
import urllib.error
import urllib.request

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
GEMINI_DEFAULT_MODELS = "gemini-2.5-flash,gemini-2.5-flash-lite,gemini-flash-latest"


def _session_key():
    """Read a visitor-supplied key from Streamlit session_state if running in web UI."""
    try:
        import streamlit as st
        return (st.session_state.get("user_api_key") or "").strip()
    except Exception:
        return ""


def _call(base, key, model, prompt):
    body = json.dumps({
        "model": model,
        "temperature": 0.2,
        "max_tokens": 8000,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")
    req = urllib.request.Request(
        base.rstrip("/") + "/chat/completions",
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
        },
    )
    with urllib.request.urlopen(req, timeout=90) as resp:
        return json.loads(resp.read().decode("utf-8"))["choices"][0]["message"]["content"]


def ask(prompt):
    user_key = _session_key()
    if user_key:
        key = user_key
        base = os.environ.get("NEBIUS_BASE_URL", GEMINI_BASE_URL)
        raw_models = (
            os.environ.get("NEBIUS_MODELS")
            or os.environ.get("NEBIUS_MODEL")
            or GEMINI_DEFAULT_MODELS
        )
    else:
        key = os.environ.get("NEBIUS_API_KEY")
        if not key:
            return None
        base = os.environ.get(
            "NEBIUS_BASE_URL", "https://api.tokenfactory.nebius.com/v1/"
        )
        raw_models = (
            os.environ.get("NEBIUS_MODELS")
            or os.environ.get("NEBIUS_MODEL")
            or "nvidia/Nemotron-3-Nano-30B-A3B"
        )

    models = [m.strip() for m in raw_models.split(",") if m.strip()]
    last_err = None
    for i, model in enumerate(models):
        for attempt in range(2):
            try:
                return _call(base, key, model, prompt)
            except urllib.error.HTTPError as e:
                last_err = e
                if e.code in (429, 403, 404):
                    break  # limit reached / model unavailable; try next model
                if attempt == 0:
                    time.sleep(3)
            except Exception as e:
                last_err = e
                if attempt == 0:
                    time.sleep(3)  # timeout or network blip
        if i + 1 < len(models):
            print(f"({model} unavailable: {last_err}. Trying {models[i + 1]})")
    print(f"(LLM unavailable, using plain search: {last_err})")
    return None


def extract_json(text):
    """Pull the first JSON object/list out of a model reply (ignores extra chatter)."""
    if not text:
        return None
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S)
    m = re.search(r"(\{.*\}|\[.*\])", text, flags=re.S)
    try:
        return json.loads(m.group(1)) if m else None
    except ValueError:
        return None
