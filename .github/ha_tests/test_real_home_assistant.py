"""The integration inside a genuine Home Assistant core.

They need Home Assistant and pytest-homeassistant-custom-component. The shared
engine installs both for every release the Compatibility workflow lists; to run them
locally: python .engine/.scripts/ha_matrix.py run 2026.9.4
"""
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

pytest.importorskip("pytest_homeassistant_custom_component")

from homeassistant.config_entries import ConfigEntryState  # noqa: E402
from homeassistant.helpers import entity_registry as er  # noqa: E402
from homeassistant.helpers import instance_id  # noqa: E402
from homeassistant.setup import async_setup_component  # noqa: E402
from homeassistant.util import dt as dt_util  # noqa: E402
from pytest_homeassistant_custom_component.common import MockConfigEntry  # noqa: E402

DOMAIN = next((Path(__file__).resolve().parents[2] / "custom_components").iterdir()).name
NOTIFICATION = f"custom_components.{DOMAIN}.manager.persistent_notification"


def at(year, month, day):
    """Pretend it is noon of the given day (the integration reads `dt_util.now()`)."""
    return patch.object(dt_util, "now", return_value=datetime(year, month, day, 12, tzinfo=dt_util.DEFAULT_TIME_ZONE))


async def setup_entry(hass, **data):
    data.setdefault("country", "RU")
    entry = MockConfigEntry(domain=DOMAIN, title="Car", data=data)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def unload(hass, entry):
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


def entity_id(hass, entry, platform, key):
    found = er.async_get(hass).async_get_entity_id(platform, DOMAIN, f"{entry.entry_id}_{key}")
    assert found, f"{platform} {key} is not registered"
    return found


def recommendation(hass, entry):
    return hass.states.get(entity_id(hass, entry, "sensor", "recommendation"))


def forecast(start, *lows_highs):
    return [
        {"datetime": (start + timedelta(days=i)).isoformat(), "templow": low, "temperature": high, "condition": "cloudy"}
        for i, (low, high) in enumerate(lows_highs)
    ]


# --- config flow ----------------------------------------------------------------


async def test_user_flow_creates_an_entry(hass, hass_storage):
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    assert result["type"] == "form"
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"name": "Golf", "country": "DE"})
    assert result["type"] == "create_entry"
    assert result["title"] == "Golf"
    assert result["data"]["country"] == "DE"
    await hass.async_block_till_done()
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    await unload(hass, entry)


async def test_canadian_setup_asks_for_the_region(hass, hass_storage):
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"name": "Car", "country": "CA"})
    assert result["type"] == "form" and result["step_id"] == "region"
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"region": "QC"})
    assert result["type"] == "create_entry"
    assert result["data"]["region"] == "QC"
    await hass.async_block_till_done()
    await unload(hass, hass.config_entries.async_entries(DOMAIN)[0])


async def test_options_flow_overrides_the_setup(hass, hass_storage):
    entry = await setup_entry(hass, country="DE", weather_entity="weather.home")
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == "form"
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"temperature_threshold": 9.0, "forecast_days": 3, "notifications": False}
    )
    assert result["type"] == "create_entry"
    await hass.async_block_till_done()
    manager = hass.data[DOMAIN][entry.entry_id]
    assert manager.settings.temperature_threshold == 9.0
    assert manager.settings.forecast_days == 3
    assert manager.weather_entity is None  # cleared field wins over the value from the setup
    assert manager.notifications_enabled is False
    await unload(hass, entry)


# --- decisions ------------------------------------------------------------------


async def test_legal_period_means_winter_tires(hass, hass_storage):
    with at(2026, 12, 15):
        entry = await setup_entry(hass, country="RU")
        state = recommendation(hass, entry)
        assert state.state == "winter"
        assert state.attributes["reason"] == "legal_period"
        assert state.attributes["legal_status"] == "required"
        assert state.attributes["country"] == "RU"
        await unload(hass, entry)


async def test_summer_outside_the_season(hass, hass_storage):
    with at(2026, 7, 10):
        entry = await setup_entry(hass, country="RU")
        assert recommendation(hass, entry).state == "summer"
        await unload(hass, entry)


async def test_cold_outdoor_sensor_triggers_winter_tires(hass, hass_storage):
    hass.states.async_set("sensor.outdoor", "2.5", {"unit_of_measurement": "°C"})
    with at(2026, 11, 10):
        entry = await setup_entry(hass, country="DE", temperature_entity="sensor.outdoor")
        state = recommendation(hass, entry)
        assert state.state == "winter"
        assert state.attributes["reason"] == "cold_weather"
        assert state.attributes["data_source"] == "history"
        hass.states.async_set("sensor.outdoor", "21", {"unit_of_measurement": "°C"})
        await hass.async_block_till_done()
        assert recommendation(hass, entry).attributes["average_temperature"] < 21
        await unload(hass, entry)


async def test_warm_autumn_keeps_summer_tires_and_fahrenheit_is_converted(hass, hass_storage):
    hass.states.async_set("sensor.outdoor", "68", {"unit_of_measurement": "°F"})  # 20 °C
    with at(2026, 10, 10):
        entry = await setup_entry(hass, country="DE", temperature_entity="sensor.outdoor")
        state = recommendation(hass, entry)
        assert state.state == "summer"
        assert state.attributes["average_temperature"] == 20.0
        await unload(hass, entry)


async def test_forecast_of_the_weather_entity_is_used(hass, hass_storage):
    start = datetime(2026, 11, 10, tzinfo=dt_util.DEFAULT_TIME_ZONE)
    hass.states.async_set(
        "weather.home", "cloudy",
        {"temperature": 9, "temperature_unit": "°C", "forecast": forecast(start, (-2, 5), (0, 6), (1, 7))},
    )
    with at(2026, 11, 10):
        entry = await setup_entry(hass, country="DE", weather_entity="weather.home")
        state = recommendation(hass, entry)
        assert (state.state, state.attributes["reason"], state.attributes["data_source"]) == ("winter", "frost_risk", "forecast")
        await unload(hass, entry)


async def test_automatic_setup_picks_the_available_weather_entity(hass, hass_storage):
    hass.states.async_set("weather.home", "sunny", {"temperature": 15, "temperature_unit": "°C"})
    entry = await setup_entry(hass, country="DE", auto_weather=True)
    assert hass.data[DOMAIN][entry.entry_id].weather_entity == "weather.home"
    await unload(hass, entry)


# --- mounted tires and notifications --------------------------------------------


async def test_tire_change_due_and_notification(hass, hass_storage):
    with at(2026, 12, 15), patch(NOTIFICATION) as notification:
        entry = await setup_entry(hass, country="RU")
        select = entity_id(hass, entry, "select", "mounted_tires")
        due = entity_id(hass, entry, "binary_sensor", "change_due")
        assert hass.states.get(select).state == "winter"  # assumed to fit on first start
        assert hass.states.get(due).state == "off"
        notification.async_create.assert_not_called()

        await hass.services.async_call("select", "select_option", {"entity_id": select, "option": "summer"}, blocking=True)
        await hass.async_block_till_done()
        assert hass.states.get(due).state == "on"
        assert hass.states.get(due).attributes["change_to"] == "winter"
        notification.async_create.assert_called_once()

        await hass.services.async_call("select", "select_option", {"entity_id": select, "option": "winter"}, blocking=True)
        await hass.async_block_till_done()
        assert hass.states.get(due).state == "off"
        notification.async_dismiss.assert_called()
        await unload(hass, entry)


async def test_all_season_tires_never_need_a_change(hass, hass_storage):
    with at(2026, 12, 15):
        entry = await setup_entry(hass, country="RU")
        select = entity_id(hass, entry, "select", "mounted_tires")
        await hass.services.async_call("select", "select_option", {"entity_id": select, "option": "all_season"}, blocking=True)
        await hass.async_block_till_done()
        assert hass.states.get(entity_id(hass, entry, "binary_sensor", "change_due")).state == "off"
        await unload(hass, entry)


async def test_no_notification_when_switched_off(hass, hass_storage):
    with at(2026, 12, 15), patch(NOTIFICATION) as notification:
        entry = await setup_entry(hass, country="RU", notifications=False)
        select = entity_id(hass, entry, "select", "mounted_tires")
        await hass.services.async_call("select", "select_option", {"entity_id": select, "option": "summer"}, blocking=True)
        await hass.async_block_till_done()
        notification.async_create.assert_not_called()
        await unload(hass, entry)


async def test_entry_loads_and_unloads(hass, hass_storage):
    entry = await setup_entry(hass, country="DE")
    assert entry.state is ConfigEntryState.LOADED
    await unload(hass, entry)
    assert entry.state is ConfigEntryState.NOT_LOADED


# --- YAML -----------------------------------------------------------------------


async def test_yaml_configuration_becomes_entries(hass, hass_storage):
    config = {DOMAIN: [{"name": "Golf", "country": "at", "temperature_threshold": 6}, {"name": "Polo", "country": "DE"}]}
    assert await async_setup_component(hass, DOMAIN, config)
    await hass.async_block_till_done()
    entries = {entry.title: entry for entry in hass.config_entries.async_entries(DOMAIN)}
    assert set(entries) == {"Golf", "Polo"}
    assert entries["Golf"].data == {"country": "AT", "temperature_threshold": 6.0}
    for entry in entries.values():
        await unload(hass, entry)


async def test_yaml_change_updates_the_existing_entry(hass, hass_storage):
    assert await async_setup_component(hass, DOMAIN, {DOMAIN: {"name": "Golf", "country": "AT"}})
    await hass.async_block_till_done()
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "import"}, data={"name": "Golf", "country": "CH"}
    )
    assert result["type"] == "abort" and result["reason"] == "already_configured"
    await hass.async_block_till_done()
    assert len(hass.config_entries.async_entries(DOMAIN)) == 1
    assert hass.config_entries.async_get_entry(entry.entry_id).data["country"] == "CH"
    await unload(hass, entry)


async def test_bare_yaml_key_uses_the_detected_country(hass, hass_storage):
    hass.config.country = "NO"
    assert await async_setup_component(hass, DOMAIN, {DOMAIN: None})
    await hass.async_block_till_done()
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    assert entry.data["country"] == "NO"
    await unload(hass, entry)


# --- self-discovery -------------------------------------------------------------


async def own_announcement(hass):
    return SimpleNamespace(properties={"uuid": await instance_id.async_get(hass)}, name="Home", type="_home-assistant._tcp.local.")


async def discover(hass, info):
    return await hass.config_entries.flow.async_init(DOMAIN, context={"source": "zeroconf"}, data=info)


async def test_discovery_creates_the_entry_without_asking(hass, hass_storage):
    hass.config.country = "DE"
    result = await discover(hass, await own_announcement(hass))
    assert result["type"] == "create_entry"
    assert result["data"] == {"country": "DE", "auto_weather": True, "auto_discovered": True}
    await hass.async_block_till_done()
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    assert entry.state is ConfigEntryState.LOADED
    again = await discover(hass, await own_announcement(hass))
    assert again["type"] == "abort"
    await unload(hass, entry)


async def test_discovery_ignores_other_home_assistant_instances(hass, hass_storage):
    hass.config.country = "DE"
    result = await discover(hass, SimpleNamespace(properties={"uuid": "someone-else"}))
    assert result["type"] == "abort" and result["reason"] == "not_own_instance"
    assert not hass.config_entries.async_entries(DOMAIN)


async def test_discovery_leaves_existing_setups_alone(hass, hass_storage):
    hass.config.country = "DE"
    entry = await setup_entry(hass, country="AT")
    result = await discover(hass, await own_announcement(hass))
    assert result["type"] == "abort" and result["reason"] == "already_configured"
    assert len(hass.config_entries.async_entries(DOMAIN)) == 1
    await unload(hass, entry)


async def test_discovery_without_a_known_country_offers_the_form(hass, hass_storage):
    hass.config.country = None
    hass.config.time_zone = "UTC"
    result = await discover(hass, await own_announcement(hass))
    assert result["type"] == "form" and result["step_id"] == "user"
    hass.config_entries.flow.async_abort(result["flow_id"])


async def test_discovery_for_canada_asks_for_the_region(hass, hass_storage):
    hass.config.country = "CA"
    result = await discover(hass, await own_announcement(hass))
    assert result["type"] == "form"
    hass.config_entries.flow.async_abort(result["flow_id"])


async def test_removed_automatic_entry_is_not_created_again(hass, hass_storage):
    hass.config.country = "DE"
    result = await discover(hass, await own_announcement(hass))
    await hass.async_block_till_done()
    await hass.config_entries.async_remove(result["result"].entry_id)
    await hass.async_block_till_done()
    again = await discover(hass, await own_announcement(hass))
    assert again["type"] == "abort" and again["reason"] == "declined"
