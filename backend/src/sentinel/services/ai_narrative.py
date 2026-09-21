from __future__ import annotations

import json
from typing import Any

import requests

from sentinel.config import settings


def build_ai_narrative(
    analysis: dict[str, Any],
    evidence: dict[str, Any] | None,
    notes: list[dict[str, Any]] | None,
    mode: str,
    provider: str | None = None,
    model: str | None = None,
<<<<<<< HEAD
    api_url: str | None = None,
    api_key: str | None = None,
=======
>>>>>>> f27ff144a8ecc8ace559ec86547e0cd2d9dd3674
) -> list[dict[str, Any]] | None:
    provider = (provider or settings.llm_provider or "none").lower()
    if provider in {"none", "off"}:
        return None

<<<<<<< HEAD
    api_url = api_url or settings.llm_api_url
    api_key = api_key or settings.llm_api_key
=======
    api_url = settings.llm_api_url
    api_key = settings.llm_api_key
>>>>>>> f27ff144a8ecc8ace559ec86547e0cd2d9dd3674
    if not api_url or not api_key:
        return None

    prompt = _build_prompt(analysis, evidence, notes, mode)
    if provider == "anthropic":
        content = _call_anthropic(api_url, api_key, model or settings.llm_model, prompt)
    else:
        content = _call_openai(api_url, api_key, model or settings.llm_model, prompt)
    if not content:
        return None

    try:
        payload = json.loads(content)
    except json.JSONDecodeError:
        return None

    sections = []
    for key, title in _section_order():
        body = payload.get(key)
        if not body:
            continue
        sections.append({"title": title, "body": body})
    return sections or None


def _build_prompt(
    analysis: dict[str, Any],
    evidence: dict[str, Any] | None,
    notes: list[dict[str, Any]] | None,
    mode: str,
) -> str:
    notes_text = [note.get("text") for note in (notes or []) if note.get("text")]
    payload = {
        "analysis": analysis,
        "evidence": evidence or {},
        "arbiter_notes": notes_text,
        "mode": mode,
    }
    instructions = (
        "You are an arbiter-grade reporting assistant for chess fair-play analysis. "
        "Write a neutral, non-accusatory narrative. Never claim cheating. "
        "Use cautious language and recommend human review for elevated signals. "
        "Return STRICT JSON with the following keys: "
        "overview, methodology, findings, statistical_interpretation, behavioral_signals, "
        "limitations, conclusion. Values should be short paragraphs or bullet lists."
    )
    return f"{instructions}\n\nDATA:\n{json.dumps(payload, ensure_ascii=False)}"


def _call_openai(
    api_url: str,
    api_key: str,
    model: str | None,
    prompt: str,
) -> str | None:
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    body = {
        "model": model or "default",
        "messages": [
            {"role": "system", "content": "You are a cautious fair-play report writer."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
    }
    try:
        resp = requests.post(api_url, headers=headers, json=body, timeout=settings.llm_timeout_seconds)
        if not resp.ok:
            return None
        data = resp.json()
    except Exception:
        return None

    choices = data.get("choices") or []
    if not choices:
        return None
    message = choices[0].get("message") or {}
    return message.get("content")

def _call_anthropic(
    api_url: str,
    api_key: str,
    model: str | None,
    prompt: str,
) -> str | None:
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
    }
    body = {
        "model": model or "claude-3-5-sonnet-20240620",
        "max_tokens": 800,
        "temperature": 0.2,
        "messages": [{"role": "user", "content": prompt}],
    }
    try:
        resp = requests.post(api_url, headers=headers, json=body, timeout=settings.llm_timeout_seconds)
        if not resp.ok:
            return None
        data = resp.json()
    except Exception:
        return None
    content = data.get("content") or []
    if isinstance(content, list) and content:
        return content[0].get("text")
    return None


def _section_order() -> list[tuple[str, str]]:
    return [
        ("overview", "Overview"),
        ("methodology", "Methodology"),
        ("findings", "Findings"),
        ("statistical_interpretation", "Statistical Interpretation"),
        ("behavioral_signals", "Behavioral Signals"),
        ("limitations", "Limitations"),
        ("conclusion", "Conclusion"),
    ]
