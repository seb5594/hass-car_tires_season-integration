"""Texts of the persistent notification, one JSON file per language in `messages/`."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from .engine import Reason, Season

MESSAGES_DIR = Path(__file__).parent / "messages"
FALLBACK_LANGUAGE = "en"
# Home Assistant language codes that share a translation file.
ALIASES = {"no": "nb", "nn": "nb", "zh-cn": "zh-hans", "zh-tw": "zh-hant", "zh-hk": "zh-hant"}


def language_candidates(language: str) -> List[str]:
    """The files to try for a language, most specific first (pt-BR, then pt)."""
    code = ALIASES.get(language.lower(), language)
    candidates = [code]
    if "-" in code:
        candidates.append(code.split("-")[0])
    return candidates


def load_messages(language: str) -> Dict[str, object]:
    """Read the notification texts (blocking; call it from an executor).

    Missing keys fall back to English, so a partly translated file never breaks a notification.
    """
    messages = json.loads((MESSAGES_DIR / f"{FALLBACK_LANGUAGE}.json").read_text(encoding="utf-8"))
    for candidate in language_candidates(language):
        path = next(
            (p for p in MESSAGES_DIR.glob("*.json") if p.stem.lower() == candidate.lower()), None
        )
        if path is not None:
            messages = _merge(messages, json.loads(path.read_text(encoding="utf-8")))
            break
    return messages


def _merge(base: Dict[str, object], override: Dict[str, object]) -> Dict[str, object]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            merged[key] = _merge(base[key], value)  # type: ignore[arg-type]
        else:
            merged[key] = value
    return merged


def build_notification(messages: Dict[str, object], target: Season, reason: Reason) -> Dict[str, str]:
    """Title and body for the request to change to the `target` tires."""
    action = messages["to_winter" if target is Season.WINTER else "to_summer"]
    reasons = messages["reasons"]
    return {"title": str(messages["title"]), "message": f"{action}\n\n{reasons[reason.value]}"}
