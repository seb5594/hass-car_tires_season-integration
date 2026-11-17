"""Time zone to country mapping, used when Home Assistant has no country configured."""
from __future__ import annotations

from typing import Optional

# Main time zone of each researched country; used when Home Assistant has no country set.
TIME_ZONE_COUNTRIES = {
    "Europe/Tirane": "AL", "Europe/Vienna": "AT", "Europe/Sarajevo": "BA", "Europe/Brussels": "BE",
    "Europe/Sofia": "BG", "Europe/Minsk": "BY", "Europe/Zurich": "CH", "Asia/Nicosia": "CY",
    "Europe/Prague": "CZ", "Europe/Berlin": "DE", "Europe/Copenhagen": "DK", "Europe/Tallinn": "EE",
    "Europe/Madrid": "ES", "Europe/Helsinki": "FI", "Europe/Paris": "FR", "Europe/London": "GB",
    "Europe/Athens": "GR", "Europe/Zagreb": "HR", "Europe/Budapest": "HU", "Europe/Dublin": "IE",
    "Atlantic/Reykjavik": "IS", "Europe/Rome": "IT", "Europe/Vaduz": "LI", "Europe/Vilnius": "LT",
    "Europe/Luxembourg": "LU", "Europe/Riga": "LV", "Europe/Chisinau": "MD", "Europe/Podgorica": "ME",
    "Europe/Skopje": "MK", "Europe/Amsterdam": "NL", "Europe/Oslo": "NO", "Europe/Warsaw": "PL",
    "Europe/Lisbon": "PT", "Europe/Bucharest": "RO", "Europe/Belgrade": "RS", "Europe/Moscow": "RU",
    "Europe/Stockholm": "SE", "Europe/Ljubljana": "SI", "Europe/Bratislava": "SK",
    "Europe/Istanbul": "TR", "Europe/Kyiv": "UA", "Europe/Kiev": "UA", "Asia/Tokyo": "JP",
    "Asia/Seoul": "KR", "Asia/Shanghai": "CN", "Asia/Taipei": "TW", "America/New_York": "US",
    "America/Chicago": "US", "America/Denver": "US", "America/Los_Angeles": "US",
    "America/Anchorage": "US",
}


def country_from_time_zone(time_zone: Optional[str]) -> Optional[str]:
    """The researched country that uses this IANA time zone, if there is one."""
    return TIME_ZONE_COUNTRIES.get(time_zone or "")
