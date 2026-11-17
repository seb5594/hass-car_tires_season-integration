"""Config and options flow of Car Tires Season."""
from __future__ import annotations

from typing import Any, Dict, Optional

import logging

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import selector
from homeassistant.util import slugify

from .const import (
    CONF_AUTO_DISCOVERED,
    CONF_AUTO_WEATHER,
    CONF_COUNTRY,
    CONF_FORECAST_DAYS,
    CONF_NOTIFICATIONS,
    CONF_REGION,
    CONF_TEMPERATURE_ENTITY,
    CONF_THRESHOLD,
    CONF_WEATHER_ENTITY,
    DEFAULT_NAME,
    DOMAIN,
)
from .country_names import COUNTRY_NAMES
from .discovery import async_is_own_instance, async_was_declined, detect_country
from .messages import load_messages
from .engine import DEFAULT_FORECAST_DAYS, DEFAULT_THRESHOLD
from .rules_data import RULES

CONF_NAME = "name"
_LOGGER = logging.getLogger(__name__)
FlowResult = Dict[str, Any]


def _selector_or(config: Dict[str, Any], fallback: Any) -> Any:
    """Use a UI selector when this Home Assistant knows it, otherwise a plain validator."""
    try:
        return selector.selector(config)
    except (vol.Invalid, KeyError, ValueError):
        return fallback


def _country_field() -> Any:
    names = {code: f"{COUNTRY_NAMES[code]} ({code})" for code in sorted(RULES)}
    return _selector_or({"country": {}}, vol.In(names))


def _number_field(minimum: float, maximum: float, step: float, unit: Optional[str] = None) -> Any:
    config: Dict[str, Any] = {"min": minimum, "max": maximum, "step": step, "mode": "box"}
    if unit:
        config["unit_of_measurement"] = unit
    return _selector_or({"number": config}, vol.All(vol.Coerce(float), vol.Range(minimum, maximum)))


def _entity_field(domain: str, device_class: Optional[str] = None) -> Any:
    config: Dict[str, Any] = {"domain": domain}
    if device_class:
        config["device_class"] = device_class
    return _selector_or({"entity": config}, str)


def _region_field(regions: Dict[str, Any]) -> Any:
    options = [{"value": code, "label": _REGION_NAMES.get(code, code)} for code in regions]
    return _selector_or(
        {"select": {"options": options, "mode": "dropdown"}},
        vol.In({item["value"]: item["label"] for item in options}),
    )


# Proper names of regions with their own rules; they are not translated.
_REGION_NAMES = {"QC": "Québec", "BC": "British Columbia"}


def _suggested(key: str, value: Any, optional: bool = True) -> vol.Marker:
    marker = vol.Optional if optional else vol.Required
    return marker(key, description={"suggested_value": value})


async def _default_name(hass: HomeAssistant) -> str:
    """The integration name in the language of the Home Assistant server."""
    language = getattr(hass.config, "language", "en")
    messages = await hass.async_add_executor_job(load_messages, language)
    return str(messages.get("name", DEFAULT_NAME))


def _default_weather_entity(hass: HomeAssistant) -> Optional[str]:
    entities = hass.states.async_entity_ids("weather")
    return entities[0] if entities else None


def _tuning_schema(values: Dict[str, Any]) -> Dict[Any, Any]:
    return {
        vol.Required(CONF_THRESHOLD, default=values.get(CONF_THRESHOLD, DEFAULT_THRESHOLD)): _number_field(
            -10, 20, 0.5, "°C"
        ),
        vol.Required(
            CONF_FORECAST_DAYS, default=values.get(CONF_FORECAST_DAYS, DEFAULT_FORECAST_DAYS)
        ): _number_field(1, 14, 1),
        vol.Required(CONF_NOTIFICATIONS, default=values.get(CONF_NOTIFICATIONS, True)): bool,
    }


def _sources_schema(values: Dict[str, Any], default_weather: Optional[str] = None) -> Dict[Any, Any]:
    return {
        _suggested(CONF_WEATHER_ENTITY, values.get(CONF_WEATHER_ENTITY, default_weather)): _entity_field("weather"),
        _suggested(CONF_TEMPERATURE_ENTITY, values.get(CONF_TEMPERATURE_ENTITY)): _entity_field(
            "sensor", "temperature"
        ),
    }


def _clean(user_input: Dict[str, Any]) -> Dict[str, Any]:
    """Store numbers as numbers and drop empty optional values."""
    cleaned = {key: value for key, value in user_input.items() if value not in (None, "")}
    if CONF_FORECAST_DAYS in cleaned:
        cleaned[CONF_FORECAST_DAYS] = int(cleaned[CONF_FORECAST_DAYS])
    if CONF_THRESHOLD in cleaned:
        cleaned[CONF_THRESHOLD] = float(cleaned[CONF_THRESHOLD])
    return cleaned


class CarTiresSeasonConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Ask for the car's country and weather sources."""

    VERSION = 1

    def __init__(self) -> None:
        self._data: Dict[str, Any] = {}
        self._default_title = DEFAULT_NAME

    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None) -> FlowResult:
        """First step: name, country and the optional weather sources."""
        if user_input is not None:
            self._data = _clean(user_input)
            country = self._data[CONF_COUNTRY].upper()
            self._data[CONF_COUNTRY] = country
            if country in RULES and RULES[country].regions:
                return await self.async_step_region()
            return self._create_entry()

        country = detect_country(self.hass)
        schema = {
            vol.Required(CONF_NAME, default=await _default_name(self.hass)): str,
            (
                vol.Required(CONF_COUNTRY, default=country)
                if country
                else vol.Required(CONF_COUNTRY)
            ): _country_field(),
            **_sources_schema({}, _default_weather_entity(self.hass)),
        }
        return self.async_show_form(step_id="user", data_schema=vol.Schema(schema))

    async def async_step_zeroconf(self, discovery_info: Any) -> FlowResult:
        """Set up by itself when Home Assistant discovers its own announcement.

        Only if the country is known and needs no regional choice is the entry created
        without asking; otherwise the usual form is offered as a discovered integration.
        """
        if not await async_is_own_instance(self.hass, discovery_info):
            return self.async_abort(reason="not_own_instance")
        await self.async_set_unique_id(f"{DOMAIN}_auto")
        self._abort_if_unique_id_configured()
        if self._async_current_entries():
            return self.async_abort(reason="already_configured")
        if await async_was_declined(self.hass):
            return self.async_abort(reason="declined")

        country = detect_country(self.hass)
        if country is None or (country in RULES and RULES[country].regions):
            return await self.async_step_user()
        self._default_title = await _default_name(self.hass)
        self._data = {CONF_COUNTRY: country, CONF_AUTO_WEATHER: True, CONF_AUTO_DISCOVERED: True}
        return self._create_entry()

    async def async_step_import(self, import_data: Dict[str, Any]) -> FlowResult:
        """Create or refresh an entry from the YAML configuration."""
        data = _clean(import_data)
        given_name = data.pop(CONF_NAME, None)
        name = given_name or await _default_name(self.hass)
        country = data.get(CONF_COUNTRY) or detect_country(self.hass)
        if country is None:
            _LOGGER.warning("YAML entry '%s' ignored: set `country` (no country could be detected)", name)
            return self.async_abort(reason="country_unknown")
        data[CONF_COUNTRY] = country.upper()
        unique_id = f"yaml_{slugify(given_name or 'default')}"
        await self.async_set_unique_id(unique_id)
        for entry in self._async_current_entries():
            if entry.unique_id == unique_id:
                # YAML is the source of truth: apply its current content and drop UI overrides.
                self.hass.config_entries.async_update_entry(entry, title=name, data=data, options={})
                return self.async_abort(reason="already_configured")
        return self.async_create_entry(title=name, data=data)

    async def async_step_region(self, user_input: Optional[Dict[str, Any]] = None) -> FlowResult:
        """Optional step for countries whose rules differ by region."""
        regions = RULES[self._data[CONF_COUNTRY]].regions
        if user_input is not None:
            self._data.update(_clean(user_input))
            return self._create_entry()
        schema = vol.Schema({vol.Optional(CONF_REGION): _region_field(regions)})
        return self.async_show_form(step_id="region", data_schema=schema)

    def _create_entry(self) -> FlowResult:
        title = self._data.pop(CONF_NAME, None) or self._default_title
        return self.async_create_entry(title=title, data=self._data)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> "OptionsFlowHandler":
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Change the weather sources and the tuning of an existing entry."""

    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        # Kept under a private name: newer Home Assistant versions forbid setting `config_entry`.
        self._entry = entry

    async def async_step_init(self, user_input: Optional[Dict[str, Any]] = None) -> FlowResult:
        if user_input is not None:
            # Whatever the user picks (or clears) from now on replaces the automatic choice.
            options = {**_clean(user_input), CONF_AUTO_WEATHER: False}
            for key in (CONF_REGION, CONF_WEATHER_ENTITY, CONF_TEMPERATURE_ENTITY):
                # An explicit None overrides the value chosen during setup when a field is cleared.
                options.setdefault(key, None)
            return self.async_create_entry(title="", data=options)

        values = {**self._entry.data, **self._entry.options}
        rule = RULES.get(str(values.get(CONF_COUNTRY, "")).upper())
        schema: Dict[Any, Any] = {}
        if rule is not None and rule.regions:
            schema[_suggested(CONF_REGION, values.get(CONF_REGION))] = _region_field(rule.regions)
        schema.update(_sources_schema(values))
        schema.update(_tuning_schema(values))
        return self.async_show_form(step_id="init", data_schema=vol.Schema(schema))
