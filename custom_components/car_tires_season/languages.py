"""Which researched countries back which translation.

A language ships only when the winter tire rules of at least one country that speaks it were
checked (see rules_data.py); the repository tests enforce this table.
"""
from __future__ import annotations

from typing import Dict, Tuple

LANGUAGE_COUNTRIES: Dict[str, Tuple[str, ...]] = {
    "bg": ("BG",),
    "cs": ("CZ",),
    "da": ("DK",),
    "de": ("DE", "AT", "CH", "LI", "LU"),
    "el": ("GR", "CY"),
    "en": ("GB", "IE", "US", "CA"),
    "es": ("ES",),
    "et": ("EE",),
    "fi": ("FI",),
    "fr": ("FR", "BE", "CH", "LU", "CA"),
    "hr": ("HR", "BA"),
    "hu": ("HU",),
    "is": ("IS",),
    "it": ("IT", "CH"),
    "ja": ("JP",),
    "ko": ("KR",),
    "lt": ("LT",),
    "lv": ("LV",),
    "mk": ("MK",),
    "nb": ("NO",),
    "nl": ("NL", "BE"),
    "pl": ("PL",),
    "pt": ("PT",),
    "ro": ("RO", "MD"),
    "ru": ("RU", "BY"),
    "sk": ("SK",),
    "sl": ("SI",),
    "sq": ("AL",),
    "sr": ("RS", "ME"),
    "sr-Latn": ("RS", "ME"),
    "sv": ("SE", "FI"),
    "tr": ("TR",),
    "uk": ("UA",),
    "zh-Hans": ("CN",),
    "zh-Hant": ("TW",),
}
