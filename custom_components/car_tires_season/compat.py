"""Small shims that keep one code base working from Home Assistant 2022.4 up to the newest release."""
from __future__ import annotations

import re
from typing import Any, Dict, Optional

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import __version__ as HA_VERSION
from homeassistant.core import HomeAssistant

from .const import DOMAIN


def _version_tuple(version: str) -> tuple:
    return tuple(int(part) for part in re.findall(r"\d+", version)[:2])


# Entity names and option labels come from translation files only since this release.
SUPPORTS_ENTITY_TRANSLATIONS = _version_tuple(HA_VERSION) >= (2023, 7)


def device_info(entry_id: str, name: str) -> Dict[str, Any]:
    """Describe the one service device of an entry."""
    info: Dict[str, Any] = {"identifiers": {(DOMAIN, entry_id)}, "name": name}
    try:
        from homeassistant.helpers.device_registry import DeviceEntryType

        info["entry_type"] = DeviceEntryType.SERVICE
    except ImportError:  # Home Assistant before the enum existed
        info["entry_type"] = "service"
    return info


async def async_forward_setups(hass: HomeAssistant, entry: ConfigEntry, platforms: list) -> None:
    """Load the platforms of an entry, whichever way this Home Assistant offers."""
    if hasattr(hass.config_entries, "async_forward_entry_setups"):
        await hass.config_entries.async_forward_entry_setups(entry, platforms)
    else:
        hass.config_entries.async_setup_platforms(entry, platforms)


def sensor_device_class_enum() -> Optional[Any]:
    """The `enum` sensor device class, or None on Home Assistant releases without it."""
    try:
        from homeassistant.components.sensor import SensorDeviceClass

        return getattr(SensorDeviceClass, "ENUM", None)
    except ImportError:
        return None
