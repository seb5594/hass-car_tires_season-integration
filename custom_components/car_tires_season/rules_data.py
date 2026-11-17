"""Researched winter tire rules per country (ISO 3166-1 alpha-2).

How to read an entry: `window` is the legal period for countries with a seasonal duty and
the practical winter season for all others (the latter is not law). The review date and the
sources behind each entry are listed in docs/COUNTRY_RULES.md, which is generated from this
file by `python .github/checks/country_rules_doc.py --write`.

Confidence: "high" = several current sources agree, "medium" = few sources or small
differences between them, "low" = only weak sources were found.
"""
from __future__ import annotations

from typing import Dict, Optional, Tuple, Union

from .calendar_utils import Anchor, Window, easter, fixed
from .rules import NORTHERN_DEFAULT_WINDOW, Obligation, Rule, generic_rule

CHECKED = "2026-11-17"

# Sources shared by many countries.
ADAC = "https://www.adac.de/rund-ums-fahrzeug/reifen/sicherheit/winterreifen-schneekette-ausland/"
EVZ = "https://www.evz.de/de/verbraucherthemen/auto/fahren/winterreifen/"
CONTINENTAL = "https://www.continental-tires.com/au/en/tyre-knowledge/winter-tire-laws/"
PIRELLI = (
    "https://www.pirelli.com/global/en-ww/life/sustainability/road-safety/"
    "winter-safety-changing-winter-tyres-what-the-law-states-country-by-country-52968/"
)

DayMonth = Tuple[int, int]
Edge = Union[DayMonth, Anchor]


def _anchor(edge: Edge) -> Anchor:
    return edge if isinstance(edge, Anchor) else fixed(*edge)


def _rule(
    country: str,
    obligation: Obligation,
    start: Optional[Edge],
    end: Optional[Edge],
    confidence: str,
    *sources: str,
    regions: Optional[Dict[str, Rule]] = None,
) -> Rule:
    """Build a rule; `start`/`end` of None mean the generic default window."""
    window = NORTHERN_DEFAULT_WINDOW if start is None else Window(_anchor(start), _anchor(end))
    return Rule(
        country=country,
        obligation=obligation,
        window=window,
        confidence=confidence,
        checked=CHECKED,
        sources=sources,
        regions=regions or {},
    )


NONE, COND = Obligation.NONE, Obligation.CONDITIONS
SEASON_COND, SEASON, REGIONAL = (
    Obligation.SEASON_CONDITIONS,
    Obligation.SEASON,
    Obligation.REGIONAL_SEASON,
)

_CANADA_PROVINCES = {
    "QC": _rule(
        "CA", SEASON, (12, 1), (3, 15), "high",
        "https://www.continental-tires.com/ca/en/b2c/tire-knowledge/winter-tire-laws-in-canada.html",
        "https://www.guideautoweb.com/en/articles/72423/where-and-when-are-winter-tires-mandatory-in-canada",
    ),
    "BC": _rule(
        "CA", REGIONAL, (10, 1), (3, 31), "high",
        "https://www.cbc.ca/1.6196264",
        "https://www.michelin.ca/en/auto/learn/preparation-for-winter/when-should-you-put-on-winter-tires-in-canada",
    ),
}

RULES: Dict[str, Rule] = {
    rule.country: rule
    for rule in (
        # --- Europe ---------------------------------------------------------------
        _rule("AL", NONE, (11, 1), (4, 30), "medium", CONTINENTAL),
        _rule("AT", SEASON_COND, (11, 1), (4, 15), "high", ADAC, EVZ, CONTINENTAL),
        _rule("BA", SEASON, (11, 15), (4, 15), "medium", CONTINENTAL, "https://www.semperit.com/car/service/winter-tyres-special"),
        _rule("BE", NONE, (10, 1), (4, 30), "high", EVZ, CONTINENTAL, ADAC),
        _rule(
            "BG", SEASON, (11, 15), (3, 1), "high", EVZ, PIRELLI, "https://sofiaglobe.com/?p=125459",
        ),
        _rule(
            "BY", SEASON, (12, 1), (3, 1), "high", CONTINENTAL,
            "https://lepel.vitebsk-region.gov.by/napominaem-s-1-dekabrja-po-1-marta-transportnye-sredstva-dolzhny-byt-oborudovany-zimnimi-shinami-na-vsex-30336/en",
        ),
        _rule("CH", NONE, (10, 1), easter(), "high", ADAC, EVZ, CONTINENTAL),
        _rule("CY", NONE, None, None, "medium", EVZ, CONTINENTAL),
        _rule("CZ", SEASON_COND, (11, 1), (3, 31), "high", ADAC, EVZ, CONTINENTAL),
        _rule(
            "DE", COND, (10, 1), easter(), "high", EVZ, ADAC, CONTINENTAL,
            "https://www.gesetze-im-internet.de/stvo_2013/__2.html",
            "https://transport-online.de/news/reifenwechsel-von-oktober-bis-ostern-wann-winterreifen-pflicht-sind-102777.html",
        ),
        _rule("DK", COND, (11, 1), (4, 15), "high", EVZ, ADAC),
        _rule("EE", SEASON, (12, 1), (3, 1), "high", ADAC, EVZ, CONTINENTAL),
        _rule("ES", NONE, None, None, "high", EVZ, CONTINENTAL),
        _rule("FI", SEASON_COND, (11, 1), (3, 31), "high", ADAC, EVZ, CONTINENTAL),
        _rule("FR", REGIONAL, (11, 1), (3, 31), "high", ADAC, EVZ, CONTINENTAL),
        _rule("GB", NONE, None, None, "high", ADAC, EVZ, CONTINENTAL),
        _rule("GR", NONE, (10, 15), (3, 15), "medium", EVZ, PIRELLI),
        _rule("HR", SEASON, (11, 15), (4, 15), "high", ADAC, EVZ, CONTINENTAL),
        _rule("HU", NONE, None, None, "high", EVZ, CONTINENTAL),
        _rule("IE", NONE, None, None, "high", EVZ, CONTINENTAL),
        _rule("IS", NONE, (11, 1), (4, 14), "medium", EVZ),
        _rule("IT", REGIONAL, (11, 15), (4, 15), "high", ADAC, EVZ, CONTINENTAL),
        _rule("LI", NONE, (10, 1), easter(), "medium", CONTINENTAL),
        _rule(
            "LT", SEASON, (11, 10), (3, 31), "high", EVZ,
            "https://reidasofficial.lt/patarimai-ir-rekomendacijos/keliu-eismo-taisykles-naujienos/ziemines-padangos-2025-2026-kada-privalomos-ir-kokios-baudos/",
            "https://www.tv3.lt/gaires/ziemines-padangos",
        ),
        _rule("LU", COND, None, None, "high", ADAC, EVZ, CONTINENTAL),
        _rule("LV", SEASON, (12, 1), (3, 1), "high", ADAC, EVZ, CONTINENTAL),
        _rule("MD", SEASON_COND, (12, 1), (3, 31), "medium", CONTINENTAL),
        _rule("ME", SEASON, (11, 15), (3, 31), "medium", CONTINENTAL, PIRELLI),
        _rule("MK", SEASON, (11, 15), (3, 15), "medium", CONTINENTAL, PIRELLI),
        _rule("NL", NONE, None, None, "high", EVZ, ADAC, CONTINENTAL),
        _rule("NO", COND, (11, 1), easter(7), "high", ADAC, EVZ, CONTINENTAL),
        _rule("PL", NONE, (11, 1), (4, 1), "high", EVZ, CONTINENTAL),
        _rule("PT", NONE, None, None, "high", EVZ, CONTINENTAL),
        _rule("RO", COND, None, None, "high", ADAC, EVZ, CONTINENTAL),
        _rule("RS", SEASON_COND, (11, 1), (4, 1), "high", ADAC, CONTINENTAL, PIRELLI),
        _rule(
            "RU", SEASON, (12, 1), (2, 29), "high", CONTINENTAL,
            "https://goszakupki.tatarstan.ru/eng/index.htm/news/2364881.htm",
            "https://www1.ru/en/news/2025/12/01/rossiian-mogut-nacat-strafovat-za-ezdu-na-letnix-sinax-novyi-zakon-vstupil-v-silu-v-rossii.amp.html",
        ),
        _rule("SE", SEASON_COND, (12, 1), (3, 31), "high", ADAC, EVZ, CONTINENTAL),
        _rule("SI", SEASON, (11, 15), (3, 15), "high", ADAC, EVZ, CONTINENTAL),
        _rule("SK", SEASON_COND, (11, 15), (3, 31), "medium", ADAC, CONTINENTAL, EVZ),
        _rule(
            "TR", NONE, (11, 15), (4, 15), "medium",
            "https://www.turkiyetoday.com/nation/all-about-turkiyes-updated-winter-tire-rules-as-5-month-period-begins-3209898",
            CONTINENTAL,
        ),
        _rule(
            "UA", NONE, None, None, "medium",
            "https://unn.ua/en/news/replacing-summer-tires-with-winter-tires-when-it-should-be-done-and-whether-there-are-penalties",
        ),
        # --- Rest of the world ------------------------------------------------------
        _rule(
            "CA", NONE, None, None, "medium",
            "https://www.guideautoweb.com/en/articles/72423/where-and-when-are-winter-tires-mandatory-in-canada",
            "https://en.wikipedia.org/wiki/Snow_tire",
            regions=_CANADA_PROVINCES,
        ),
        _rule(
            "CN", NONE, None, None, "low",
            "https://tyremap.com/tyre-laws/china/",
        ),
        _rule(
            "JP", COND, None, None, "medium",
            "https://www.pref.nagano.lg.jp/police/english/winter-road/act.html",
            "https://en.wikipedia.org/wiki/Snow_tire",
        ),
        _rule(
            "KR", NONE, None, None, "low",
            "https://tyremap.com/answers/winter-tyres-south-korea/",
        ),
        _rule(
            "TW", NONE, None, None, "medium",
            "https://www.taiwannews.com.tw/en/news/4098827",
            "https://taipeitimes.com/News/taiwan/archives/2025/01/29/2003831013",
        ),
        _rule("US", NONE, None, None, "medium", "https://en.wikipedia.org/wiki/Snow_tire"),
    )
}


def rule_for(country: str, region: Optional[str], southern_hemisphere: bool) -> Rule:
    """Return the rule for a country (and region), or a generic one when none was researched."""
    rule = RULES.get(country.upper())
    if rule is None:
        return generic_rule(country.upper(), southern_hemisphere)
    return rule.for_region(region)
