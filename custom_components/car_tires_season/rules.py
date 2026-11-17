"""The legal model behind the recommendation: what a country demands, and when."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional, Tuple

from .calendar_utils import Window, fixed


class Obligation(str, Enum):
    """How a country regulates winter tires on passenger cars."""

    NONE = "none"  # No legal duty; the window is only a practical recommendation.
    CONDITIONS = "conditions"  # Required whenever winter road conditions occur, in any month.
    SEASON_CONDITIONS = "season_conditions"  # Required in winter conditions inside the legal period.
    SEASON = "season"  # Required inside the legal period, regardless of the weather.
    REGIONAL_SEASON = "regional_season"  # Required inside the period on signposted roads or in zones.


PERIOD_OBLIGATIONS = frozenset(
    {Obligation.SEASON_CONDITIONS, Obligation.SEASON, Obligation.REGIONAL_SEASON}
)

# Used for every country without a researched rule: temperature decides, the calendar only guards.
NORTHERN_DEFAULT_WINDOW = Window(fixed(11, 1), fixed(3, 31))
SOUTHERN_DEFAULT_WINDOW = Window(fixed(6, 1), fixed(9, 30))


@dataclass(frozen=True)
class Rule:
    """The winter tire regulation of one country (or of one region of it)."""

    country: str
    obligation: Obligation
    # The legal period if the obligation has one, otherwise the practical winter season.
    window: Window
    # "high": several current sources agree; "medium": sources differ slightly or are few;
    # "none": no rule was researched (generic fallback).
    confidence: str = "none"
    # ISO date of the last review of the sources below.
    checked: str = ""
    sources: Tuple[str, ...] = ()
    # Regional variants, selectable by the user (e.g. Canadian provinces).
    regions: Dict[str, "Rule"] = field(default_factory=dict)

    @property
    def has_legal_period(self) -> bool:
        return self.obligation in PERIOD_OBLIGATIONS

    @property
    def is_researched(self) -> bool:
        return self.confidence != "none"

    def for_region(self, region: Optional[str]) -> "Rule":
        """Return the variant of a region, or this rule when the region is unknown."""
        return self.regions.get(region or "", self)


def generic_rule(country: str, southern_hemisphere: bool) -> Rule:
    """The fallback for a country that has no researched rule."""
    window = SOUTHERN_DEFAULT_WINDOW if southern_hemisphere else NORTHERN_DEFAULT_WINDOW
    return Rule(country=country, obligation=Obligation.NONE, window=window)
