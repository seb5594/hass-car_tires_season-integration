"""The sensor that tells which tires fit best today."""
from __future__ import annotations

from typing import Any, Dict, Optional

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .compat import sensor_device_class_enum
from .const import DOMAIN
from .engine import Season
from .entity import TireSeasonEntity
from .manager import TireSeasonManager

ICONS = {Season.WINTER: "mdi:snowflake", Season.SUMMER: "mdi:white-balance-sunny"}


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    async_add_entities([RecommendationSensor(hass.data[DOMAIN][entry.entry_id])])


class RecommendationSensor(TireSeasonEntity, SensorEntity):
    """State is `summer` or `winter`; the attributes explain why."""

    fallback_name = "Recommended tires"

    def __init__(self, manager: TireSeasonManager) -> None:
        super().__init__(manager, "recommendation")
        enum_class = sensor_device_class_enum()
        if enum_class is not None:
            self._attr_device_class = enum_class
            self._attr_options = [season.value for season in Season]

    @property
    def native_value(self) -> Optional[str]:
        recommendation = self.manager.recommendation
        return recommendation.season.value if recommendation else None

    @property
    def icon(self) -> str:
        recommendation = self.manager.recommendation
        return ICONS[recommendation.season] if recommendation else ICONS[Season.SUMMER]

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        recommendation = self.manager.recommendation
        if recommendation is None:
            return {}
        rule = self.manager.rule
        return {
            "reason": recommendation.reason.value,
            "country": rule.country,
            "legal_obligation": rule.obligation.value,
            "legal_status": recommendation.legal_status.value,
            "season_start": recommendation.window_start.isoformat(),
            "season_end": recommendation.window_end.isoformat(),
            "in_season": recommendation.in_window,
            "average_temperature": recommendation.average_temperature,
            "minimum_temperature": recommendation.minimum_temperature,
            "data_source": recommendation.data_source,
            "rule_confidence": rule.confidence,
            "rule_sources": list(rule.sources),
        }
