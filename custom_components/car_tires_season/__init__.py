"""Car Tires Season: tells when to switch between summer and winter tires."""
from __future__ import annotations

from typing import Any, Dict

import voluptuous as vol
from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv

from .compat import async_forward_setups
from .const import (
    CONF_AUTO_DISCOVERED,
    CONF_COUNTRY,
    CONF_FORECAST_DAYS,
    CONF_NOTIFICATIONS,
    CONF_REGION,
    CONF_TEMPERATURE_ENTITY,
    CONF_THRESHOLD,
    CONF_WEATHER_ENTITY,
    DOMAIN,
    PLATFORMS,
)
from .discovery import async_remember_declined
from .manager import TireSeasonManager

# Every key is optional: `car_tires_season:` alone is valid and uses the detected country.
YAML_ENTRY_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_NAME): cv.string,
        vol.Optional(CONF_COUNTRY): vol.All(cv.string, vol.Upper, vol.Length(min=2, max=2)),
        vol.Optional(CONF_REGION): cv.string,
        vol.Optional(CONF_WEATHER_ENTITY): cv.entity_id,
        vol.Optional(CONF_TEMPERATURE_ENTITY): cv.entity_id,
        vol.Optional(CONF_THRESHOLD): vol.All(vol.Coerce(float), vol.Range(min=-10, max=20)),
        vol.Optional(CONF_FORECAST_DAYS): vol.All(vol.Coerce(int), vol.Range(min=1, max=14)),
        vol.Optional(CONF_NOTIFICATIONS): cv.boolean,
    }
)


def _as_entry_list(value: Any) -> list:
    """A bare `car_tires_season:` means one entry with defaults; a mapping means one entry."""
    return [{}] if value is None else cv.ensure_list(value)


CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: vol.All(_as_entry_list, [YAML_ENTRY_SCHEMA])},
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config: Dict[str, Any]) -> bool:
    """Turn the optional YAML configuration into config entries."""
    for item in config.get(DOMAIN, []):
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN, context={"source": SOURCE_IMPORT}, data=dict(item)
            )
        )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up one car or location from a config entry."""
    manager = TireSeasonManager(hass, entry)
    await manager.async_start()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = manager
    entry.async_on_unload(entry.add_update_listener(_async_reload_on_change))
    await async_forward_setups(hass, entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry and stop its background work."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        await hass.data[DOMAIN].pop(entry.entry_id).async_stop()
    return unloaded


async def _async_reload_on_change(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Apply changed options by reloading the entry."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Respect the user's decision: an entry created by self-discovery is never created again."""
    if entry.data.get(CONF_AUTO_DISCOVERED):
        await async_remember_declined(hass)
