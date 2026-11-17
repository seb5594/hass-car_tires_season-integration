"""The select that records which tires are on the car."""
from __future__ import annotations

from typing import Optional

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .entity import TireSeasonEntity
from .manager import MOUNTED_OPTIONS, TireSeasonManager


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    async_add_entities([MountedTiresSelect(hass.data[DOMAIN][entry.entry_id])])


class MountedTiresSelect(TireSeasonEntity, SelectEntity):
    """Change it when the tires are swapped; this switches the change-due state off."""

    fallback_name = "Mounted tires"
    _attr_icon = "mdi:car-wheel"
    _attr_options = MOUNTED_OPTIONS

    def __init__(self, manager: TireSeasonManager) -> None:
        super().__init__(manager, "mounted_tires")

    @property
    def current_option(self) -> Optional[str]:
        return self.manager.mounted

    async def async_select_option(self, option: str) -> None:
        await self.manager.async_set_mounted(option)
