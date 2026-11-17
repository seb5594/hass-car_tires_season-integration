"""Reads temperatures and forecasts from weather and sensor entities."""
from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.util import dt as dt_util

from .engine import DayWeather

_LOGGER = logging.getLogger(__name__)

SNOW_CONDITIONS = frozenset({"snowy", "snowy-rainy"})
NO_VALUE = ("unknown", "unavailable", "none", "")
FORECAST_TYPES = ("daily", "twice_daily", "hourly")


def parse_float(value: Any) -> Optional[float]:
    """Convert a state or attribute to a float, or None when it is no number."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def to_celsius(value: float, unit: Optional[str]) -> float:
    """Convert a temperature in the given unit to °C."""
    normalized = (unit or "").strip().upper().replace("°", "")
    if normalized == "F":
        return (value - 32) * 5 / 9
    if normalized == "K":
        return value - 273.15
    return value


def _system_unit(hass: HomeAssistant) -> str:
    return str(getattr(hass.config.units, "temperature_unit", "°C"))


def read_current_temperature(hass: HomeAssistant, entity_id: Optional[str]) -> Optional[float]:
    """The current temperature in °C of a weather entity or a temperature sensor."""
    state = hass.states.get(entity_id) if entity_id else None
    if state is None or str(state.state).lower() in NO_VALUE:
        return None
    if entity_id.startswith("weather."):
        value = parse_float(state.attributes.get("temperature"))
        unit = state.attributes.get("temperature_unit") or _system_unit(hass)
    else:
        value = parse_float(state.state)
        unit = state.attributes.get("unit_of_measurement") or _system_unit(hass)
    return None if value is None else to_celsius(value, unit)


def is_snowing(hass: HomeAssistant, entity_id: Optional[str]) -> bool:
    """Does the weather entity report snow right now?"""
    state = hass.states.get(entity_id) if entity_id else None
    return state is not None and state.state in SNOW_CONDITIONS


async def _async_forecast_items(hass: HomeAssistant, entity_id: str) -> Tuple[List[Dict[str, Any]], str]:
    """The raw forecast list of a weather entity and the unit of its temperatures.

    Older Home Assistant versions keep the forecast in a state attribute, newer ones only
    hand it out through the `weather.get_forecasts` service.
    """
    state = hass.states.get(entity_id)
    if state is None:
        return [], _system_unit(hass)
    unit = state.attributes.get("temperature_unit") or _system_unit(hass)
    legacy = state.attributes.get("forecast")
    if isinstance(legacy, list) and legacy:
        return legacy, unit
    if not hass.services.has_service("weather", "get_forecasts"):
        return [], unit
    for forecast_type in FORECAST_TYPES:
        try:
            response = await hass.services.async_call(
                "weather",
                "get_forecasts",
                {"entity_id": entity_id, "type": forecast_type},
                blocking=True,
                return_response=True,
            )
        except HomeAssistantError as err:
            _LOGGER.debug("%s offers no %s forecast: %s", entity_id, forecast_type, err)
            continue
        forecast = ((response or {}).get(entity_id) or {}).get("forecast")
        if forecast:
            return forecast, unit
    return [], unit


def _as_local_date(value: Any) -> Optional[date]:
    moment = value if isinstance(value, datetime) else dt_util.parse_datetime(str(value or ""))
    return None if moment is None else dt_util.as_local(moment).date()


def aggregate_forecast(
    items: List[Dict[str, Any]], unit: str, today: date, days: int
) -> List[DayWeather]:
    """Fold daily, twice-daily or hourly forecast items into one entry per local day."""
    last_day = today + timedelta(days=days - 1)
    per_day: Dict[date, DayWeather] = {}
    for item in items:
        day = _as_local_date(item.get("datetime"))
        if day is None or not today <= day <= last_day:
            continue
        values = [
            to_celsius(value, unit)
            for value in (parse_float(item.get("temperature")), parse_float(item.get("templow")))
            if value is not None
        ]
        if not values:
            continue
        snow = item.get("condition") in SNOW_CONDITIONS
        known = per_day.get(day)
        per_day[day] = DayWeather(
            day,
            min(values + ([known.minimum] if known else [])),
            max(values + ([known.maximum] if known else [])),
            snow or (known is not None and known.snow),
        )
    return [per_day[day] for day in sorted(per_day)]


async def async_daily_forecast(
    hass: HomeAssistant, entity_id: str, today: date, days: int
) -> List[DayWeather]:
    """The forecast of the next `days` days (today included), one entry per day."""
    items, unit = await _async_forecast_items(hass, entity_id)
    return aggregate_forecast(items, unit, today, days)
