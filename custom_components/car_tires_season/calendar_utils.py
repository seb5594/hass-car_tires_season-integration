"""Date helpers: movable holidays and season windows that may span a new year."""
from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional, Tuple

DateSpan = Tuple[date, date]


def easter_sunday(year: int) -> date:
    """Return the date of Western Easter Sunday (anonymous Gregorian algorithm)."""
    golden, century = year % 19, year // 100
    year_in_century = year % 100
    leap_corr = (century - (century + 8) // 25 + 1) // 3
    epact = (19 * golden + century - century // 4 - leap_corr + 15) % 30
    weekday = (32 + 2 * (century % 4) + 2 * (year_in_century // 4) - epact - year_in_century % 4) % 7
    correction = (golden + 11 * epact + 22 * weekday) // 451
    month, day = divmod(epact + weekday - 7 * correction + 114, 31)
    return date(year, month, day + 1)


@dataclass(frozen=True)
class Anchor:
    """A day of the year: a fixed month/day, or a number of days around Easter Sunday."""

    month: int = 0
    day: int = 0
    easter_offset: Optional[int] = None

    def resolve(self, year: int) -> date:
        """Return the concrete date in the given year (a too-large day is clamped, e.g. 29 Feb)."""
        if self.easter_offset is not None:
            return easter_sunday(year) + timedelta(days=self.easter_offset)
        return date(year, self.month, min(self.day, calendar.monthrange(year, self.month)[1]))


def fixed(month: int, day: int) -> Anchor:
    """Anchor on a calendar day."""
    return Anchor(month=month, day=day)


def easter(offset_days: int = 0) -> Anchor:
    """Anchor on Easter Sunday plus an offset in days."""
    return Anchor(easter_offset=offset_days)


@dataclass(frozen=True)
class Window:
    """A yearly period from `start` to `end` (inclusive). It may reach into the next year."""

    start: Anchor
    end: Anchor

    def span_starting_in(self, year: int) -> DateSpan:
        """Return the period that begins in `year`."""
        start = self.start.resolve(year)
        end_year = year if self.end.resolve(year) >= start else year + 1
        return start, self.end.resolve(end_year)

    def current_or_next(self, day: date) -> DateSpan:
        """Return the period containing `day`, or the next one when `day` lies between periods."""
        for year in (day.year - 1, day.year, day.year + 1):
            span = self.span_starting_in(year)
            if span[1] >= day:
                return span
        raise AssertionError("unreachable: a period always ends within two years")

    def contains(self, day: date, margin_days: int = 0) -> bool:
        """Is `day` inside a period, optionally widened by `margin_days` at both ends?"""
        start, end = self.current_or_next(day - timedelta(days=margin_days))
        return start - timedelta(days=margin_days) <= day <= end + timedelta(days=margin_days)
