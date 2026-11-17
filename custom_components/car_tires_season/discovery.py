"""Self-discovery: set the integration up by itself after it was installed.

Home Assistant announces itself via mDNS (`_home-assistant._tcp.local.`) and matches that
announcement against the `zeroconf` entries of every installed integration. Listing the
service type in our manifest therefore starts a config flow on each instance once, without
any user action. The flow only accepts the announcement of its own instance.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import DOMAIN, STORAGE_VERSION
from .timezones import country_from_time_zone

DECLINED_STORE_KEY = f"{DOMAIN}.discovery"


def detect_country(hass: HomeAssistant) -> Optional[str]:
    """The country of this installation: the configured one, else derived from the time zone."""
    configured = getattr(hass.config, "country", None)
    if configured:
        return str(configured).upper()
    return country_from_time_zone(hass.config.time_zone)


def discovery_properties(discovery_info: Any) -> Dict[str, Any]:
    """The mDNS properties of a discovery payload (an object in newer, a dict in older versions)."""
    properties = getattr(discovery_info, "properties", None)
    if properties is None and isinstance(discovery_info, dict):
        properties = discovery_info.get("properties")
    return dict(properties or {})


async def async_is_own_instance(hass: HomeAssistant, discovery_info: Any) -> bool:
    """Is the announcement the one of this very Home Assistant (and not of another one)?"""
    from homeassistant.helpers import instance_id

    announced = discovery_properties(discovery_info).get("uuid")
    return bool(announced) and announced == await instance_id.async_get(hass)


async def async_was_declined(hass: HomeAssistant) -> bool:
    """Has the user removed an automatically created entry before?"""
    stored = await Store(hass, STORAGE_VERSION, DECLINED_STORE_KEY).async_load()
    return bool(stored and stored.get("declined"))


async def async_remember_declined(hass: HomeAssistant) -> None:
    """Remember that the user does not want the automatic setup, so it never comes back."""
    await Store(hass, STORAGE_VERSION, DECLINED_STORE_KEY).async_save({"declined": True})
