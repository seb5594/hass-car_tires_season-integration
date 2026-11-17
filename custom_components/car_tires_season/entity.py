"""Base class shared by all entities of the integration."""
from __future__ import annotations

from homeassistant.core import callback
from homeassistant.helpers.entity import Entity

from .compat import SUPPORTS_ENTITY_TRANSLATIONS, device_info
from .manager import TireSeasonManager


class TireSeasonEntity(Entity):
    """An entity that mirrors the state of a TireSeasonManager."""

    _attr_should_poll = False
    _attr_has_entity_name = True

    # Shown by Home Assistant versions that cannot translate entity names.
    fallback_name = ""

    def __init__(self, manager: TireSeasonManager, key: str) -> None:
        self.manager = manager
        self._attr_unique_id = f"{manager.entry.entry_id}_{key}"
        self._attr_translation_key = key
        self._attr_device_info = device_info(manager.entry.entry_id, manager.entry.title)
        if not SUPPORTS_ENTITY_TRANSLATIONS:
            self._attr_has_entity_name = False
            self._attr_name = f"{manager.entry.title} {self.fallback_name}"

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(self.manager.async_add_listener(self._handle_manager_update))

    @callback
    def _handle_manager_update(self) -> None:
        self.async_write_ha_state()

    @property
    def available(self) -> bool:
        return self.manager.recommendation is not None
