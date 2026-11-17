"""The decision logic: summer or winter tires today? Pure Python, no Home Assistant imports."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from enum import Enum
from statistics import mean
from typing import Dict, Iterable, List, Optional, Tuple

from .rules import Obligation, Rule

# Weather-driven switching only happens this close to the winter season of the country.
SEASON_MARGIN_DAYS = 31
# Frost thresholds in °C: entering winter is eager, leaving it needs a clear margin.
FROST_ENTER_LIMIT = 0.0
FROST_RELEASE_LIMIT = 1.0
# Extra degrees above the temperature threshold needed before winter tires are released.
RELEASE_HYSTERESIS = 1.0
DEFAULT_THRESHOLD = 7.0
DEFAULT_FORECAST_DAYS = 5


class Season(str, Enum):
    """The tire type a car should carry."""

    SUMMER = "summer"
    WINTER = "winter"


class Reason(str, Enum):
    """Why the engine came to its decision."""

    LEGAL_PERIOD = "legal_period"
    SNOW_EXPECTED = "snow_expected"
    FROST_RISK = "frost_risk"
    COLD_WEATHER = "cold_weather"
    MILD_WEATHER = "mild_weather"
    SEASON_CALENDAR = "season_calendar"
    OUTSIDE_SEASON = "outside_season"


class LegalStatus(str, Enum):
    """Whether winter tires are legally required for the user right now."""

    NOT_REQUIRED = "not_required"
    CONDITIONAL = "conditional"  # Required as soon as winter road conditions occur.
    REGIONAL = "regional"  # Required on signposted roads or in designated zones.
    REQUIRED = "required"


@dataclass(frozen=True)
class DayWeather:
    """Observed or forecast temperatures of one day, in °C."""

    day: date
    minimum: float
    maximum: float
    snow: bool = False

    @property
    def mean(self) -> float:
        return (self.minimum + self.maximum) / 2


@dataclass(frozen=True)
class Outlook:
    """The weather the decision is based on: a forecast or the recent past."""

    days: Tuple[DayWeather, ...]
    source: str  # "forecast" or "history"
    snow_now: bool = False
    current_temperature: Optional[float] = None

    @property
    def average(self) -> Optional[float]:
        return mean(day.mean for day in self.days) if self.days else None

    @property
    def minimum(self) -> Optional[float]:
        return min(day.minimum for day in self.days) if self.days else None

    @property
    def snow(self) -> bool:
        return self.snow_now or any(day.snow for day in self.days)


@dataclass(frozen=True)
class Settings:
    """User-adjustable tuning."""

    temperature_threshold: float = DEFAULT_THRESHOLD
    forecast_days: int = DEFAULT_FORECAST_DAYS


@dataclass(frozen=True)
class Recommendation:
    """The result of one evaluation."""

    season: Season
    reason: Reason
    legal_status: LegalStatus
    window_start: date
    window_end: date
    in_window: bool
    average_temperature: Optional[float] = None
    minimum_temperature: Optional[float] = None
    data_source: str = "calendar"


def _weather_decision(outlook: Outlook, was_winter: bool, settings: Settings) -> Tuple[Season, Reason]:
    """Judge by the weather, with a hysteresis so the result does not flip back and forth."""
    if outlook.snow:
        return Season.WINTER, Reason.SNOW_EXPECTED
    frost_limit = FROST_RELEASE_LIMIT if was_winter else FROST_ENTER_LIMIT
    if outlook.minimum is not None and outlook.minimum <= frost_limit:
        return Season.WINTER, Reason.FROST_RISK
    limit = settings.temperature_threshold + (RELEASE_HYSTERESIS if was_winter else 0.0)
    if outlook.average is not None and outlook.average < limit:
        return Season.WINTER, Reason.COLD_WEATHER
    return Season.SUMMER, Reason.MILD_WEATHER


def _legal_status(rule: Rule, in_window: bool, winter_conditions: bool) -> LegalStatus:
    """Translate the rule into what applies to the user today."""
    obligation = rule.obligation
    if obligation is Obligation.SEASON and in_window:
        return LegalStatus.REQUIRED
    if obligation is Obligation.REGIONAL_SEASON and in_window:
        return LegalStatus.REGIONAL
    if obligation is Obligation.CONDITIONS or (obligation is Obligation.SEASON_CONDITIONS and in_window):
        return LegalStatus.REQUIRED if winter_conditions else LegalStatus.CONDITIONAL
    return LegalStatus.NOT_REQUIRED


def recommend(
    rule: Rule,
    today: date,
    outlook: Optional[Outlook],
    previous: Optional[Season],
    settings: Settings,
) -> Recommendation:
    """Decide which tires fit today.

    Order of precedence: a legal duty that applies regardless of weather; then the weather
    (only close to the country's winter season, so a frosty July night changes nothing); and,
    when no temperature data exists at all, the calendar.
    """
    window_start, window_end = rule.window.current_or_next(today)
    in_window = window_start <= today <= window_end
    has_data = outlook is not None and bool(outlook.days)
    winter_conditions = outlook is not None and (
        outlook.snow_now
        or (outlook.current_temperature is not None and outlook.current_temperature <= FROST_ENTER_LIMIT)
    )
    status = _legal_status(rule, in_window, winter_conditions)

    base = dict(
        legal_status=status,
        window_start=window_start,
        window_end=window_end,
        in_window=in_window,
        average_temperature=_rounded(outlook.average) if has_data else None,
        minimum_temperature=_rounded(outlook.minimum) if has_data else None,
        data_source=outlook.source if has_data else "calendar",
    )

    if rule.obligation is Obligation.SEASON and in_window:
        return Recommendation(season=Season.WINTER, reason=Reason.LEGAL_PERIOD, **base)
    if has_data:
        if rule.window.contains(today, SEASON_MARGIN_DAYS):
            season, reason = _weather_decision(outlook, previous is Season.WINTER, settings)
        else:
            season, reason = Season.SUMMER, Reason.OUTSIDE_SEASON
        return Recommendation(season=season, reason=reason, **base)
    if in_window:
        return Recommendation(season=Season.WINTER, reason=Reason.SEASON_CALENDAR, **base)
    return Recommendation(season=Season.SUMMER, reason=Reason.OUTSIDE_SEASON, **base)


def _rounded(value: Optional[float]) -> Optional[float]:
    return None if value is None else round(value, 1)


@dataclass
class _DayStats:
    minimum: float
    maximum: float
    snow: bool = False


class TemperatureHistory:
    """Daily minimum and maximum of recent days, built from single readings.

    It lets a plain outdoor temperature sensor stand in for a weather forecast.
    """

    def __init__(self, keep_days: int = 14) -> None:
        self._keep_days = keep_days
        self._days: Dict[date, _DayStats] = {}

    def add(self, day: date, temperature: float, snow: bool = False) -> None:
        """Record one reading."""
        stats = self._days.get(day)
        if stats is None:
            self._days[day] = _DayStats(temperature, temperature, snow)
        else:
            stats.minimum = min(stats.minimum, temperature)
            stats.maximum = max(stats.maximum, temperature)
            stats.snow = stats.snow or snow
        for old in [d for d in self._days if d < day - timedelta(days=self._keep_days)]:
            del self._days[old]

    def recent(self, today: date, days: int) -> List[DayWeather]:
        """The last `days` days up to and including today."""
        first = today - timedelta(days=days - 1)
        return [
            DayWeather(day, stats.minimum, stats.maximum, stats.snow)
            for day, stats in sorted(self._days.items())
            if first <= day <= today
        ]

    def as_dict(self) -> Dict[str, List[object]]:
        return {
            day.isoformat(): [stats.minimum, stats.maximum, stats.snow]
            for day, stats in self._days.items()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Iterable[object]]) -> "TemperatureHistory":
        history = cls()
        for key, values in (data or {}).items():
            try:
                low, high, snow = list(values)
                history._days[date.fromisoformat(key)] = _DayStats(float(low), float(high), bool(snow))
            except (TypeError, ValueError):
                continue  # Ignore damaged entries instead of failing the setup.
        return history
