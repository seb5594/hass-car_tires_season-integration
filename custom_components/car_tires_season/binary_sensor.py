"""The binary sensor that is on while the mounted tires do not fit the season."""
from __future__ import annotations

from typing import Any, Dict

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .entity import TireSeasonEntity
from .manager import TireSeasonManager


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    async_add_entities([TireChangeDueSensor(hass.data[DOMAIN][entry.entry_id])])


class TireChangeDueSensor(TireSeasonEntity, BinarySensorEntity):
    """On when it is time to switch tires; ideal as an automation trigger."""

    fallback_name = "Tire change due"
    _attr_icon = "mdi:car-tire-alert"

    def __init__(self, manager: TireSeasonManager) -> None:
        super().__init__(manager, "change_due")

    @property
    def is_on(self) -> bool:
        return self.manager.change_target is not None

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        target = self.manager.change_target
        return {
            "change_to": target.value if target else None,
            "mounted": self.manager.mounted,
        }
