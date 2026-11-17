"""Runtime of one config entry: gathers weather, evaluates the rule, keeps state, notifies."""
from __future__ import annotations

import asyncio
import logging
import time
from datetime import timedelta
from typing import Any, Callable, Dict, List, Optional

from homeassistant.components import persistent_notification
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event, async_track_time_interval
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import (
    ALL_SEASON,
    CONF_AUTO_WEATHER,
    CONF_COUNTRY,
    CONF_FORECAST_DAYS,
    CONF_NOTIFICATIONS,
    CONF_REGION,
    CONF_TEMPERATURE_ENTITY,
    CONF_THRESHOLD,
    CONF_WEATHER_ENTITY,
    DOMAIN,
    EVALUATION_INTERVAL_SECONDS,
    FORECAST_REFRESH_SECONDS,
    STORAGE_SAVE_DELAY_SECONDS,
    STORAGE_VERSION,
)
from .engine import (
    DEFAULT_FORECAST_DAYS,
    DEFAULT_THRESHOLD,
    DayWeather,
    Outlook,
    Recommendation,
    Season,
    Settings,
    TemperatureHistory,
    recommend,
)
from .messages import build_notification, load_messages
from .rules_data import rule_for
from .weather import async_daily_forecast, is_snowing, read_current_temperature

_LOGGER = logging.getLogger(__name__)

MOUNTED_OPTIONS = [Season.SUMMER.value, Season.WINTER.value, ALL_SEASON]


class TireSeasonManager:
    """Owns everything that changes over time for one configured car or location."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        config: Dict[str, Any] = {**entry.data, **entry.options}
        self.rule = rule_for(
            config[CONF_COUNTRY], config.get(CONF_REGION), hass.config.latitude < 0
        )
        self.settings = Settings(
            temperature_threshold=float(config.get(CONF_THRESHOLD, DEFAULT_THRESHOLD)),
            forecast_days=int(config.get(CONF_FORECAST_DAYS, DEFAULT_FORECAST_DAYS)),
        )
        self.weather_entity: Optional[str] = config.get(CONF_WEATHER_ENTITY) or None
        # Without an explicit choice the automatic setup uses whichever weather entity exists.
        self._auto_weather = bool(config.get(CONF_AUTO_WEATHER)) and self.weather_entity is None
        self.temperature_entity: Optional[str] = config.get(CONF_TEMPERATURE_ENTITY) or None
        self.notifications_enabled: bool = bool(config.get(CONF_NOTIFICATIONS, True))

        self.recommendation: Optional[Recommendation] = None
        self.mounted: Optional[str] = None

        self._store: Store = Store(hass, STORAGE_VERSION, f"{DOMAIN}.{entry.entry_id}")
        self._history = TemperatureHistory()
        self._forecast: List[DayWeather] = []
        self._forecast_fetched_at: Optional[float] = None
        self._last_season: Optional[Season] = None
        self._messages: Dict[str, Any] = {}
        self._notified_for: Optional[Season] = None
        self._listeners: List[Callable[[], None]] = []
        self._unsubscribers: List[Callable[[], None]] = []
        self._state_unsubscribe: Optional[Callable[[], None]] = None
        self._started_unsubscribe: Optional[Callable[[], None]] = None
        self._lock = asyncio.Lock()

    # --- lifecycle ----------------------------------------------------------------

    async def async_start(self) -> None:
        """Restore stored state, start listening, and make the first evaluation."""
        stored = await self._store.async_load() or {}
        self._history = TemperatureHistory.from_dict(stored.get("history", {}))
        mounted = stored.get("mounted")
        self.mounted = mounted if mounted in MOUNTED_OPTIONS else None
        try:
            self._last_season = Season(stored.get("last_season"))
        except ValueError:
            self._last_season = None
        self._messages = await self.hass.async_add_executor_job(
            load_messages, getattr(self.hass.config, "language", "en")
        )

        self._resolve_weather_entity()
        self._subscribe_to_states()
        if self._auto_weather and not self.hass.is_running:
            # Weather entities of other integrations appear while Home Assistant starts.
            self._started_unsubscribe = self.hass.bus.async_listen_once(
                EVENT_HOMEASSISTANT_STARTED, self._handle_started
            )
        self._unsubscribers.append(
            async_track_time_interval(
                self.hass, self._handle_interval, timedelta(seconds=EVALUATION_INTERVAL_SECONDS)
            )
        )
        await self.async_refresh(force_forecast=True)

    async def async_stop(self) -> None:
        """Stop listening, save the state and withdraw the notification."""
        for unsubscribe in self._unsubscribers:
            unsubscribe()
        self._unsubscribers.clear()
        if self._state_unsubscribe:
            self._state_unsubscribe()
        if self._started_unsubscribe:
            self._started_unsubscribe()
        await self._store.async_save(self._data_to_store())
        self._dismiss_notification()

    # --- public state -------------------------------------------------------------

    @property
    def change_target(self) -> Optional[Season]:
        """The tires to switch to, or None if the mounted ones already fit."""
        if self.recommendation is None or self.mounted in (None, ALL_SEASON):
            return None
        if self.mounted == self.recommendation.season.value:
            return None
        return self.recommendation.season

    @callback
    def async_add_listener(self, listener: Callable[[], None]) -> Callable[[], None]:
        """Call `listener` whenever the evaluation or the mounted tires change."""
        self._listeners.append(listener)

        @callback
        def remove() -> None:
            self._listeners.remove(listener)

        return remove

    async def async_set_mounted(self, option: str) -> None:
        """Tell the integration which tires are on the car now."""
        if option not in MOUNTED_OPTIONS:
            raise ValueError(f"Unknown tire option: {option}")
        self.mounted = option
        self._publish()

    # --- evaluation ---------------------------------------------------------------

    async def async_refresh(self, force_forecast: bool = False) -> None:
        """Re-evaluate the recommendation with the latest weather data."""
        async with self._lock:
            today = dt_util.now().date()
            if self._resolve_weather_entity():
                self._subscribe_to_states()
                force_forecast = True
            await self._async_update_forecast(today, force_forecast)
            self._record_sample(today)
            previous = self.recommendation.season if self.recommendation else self._last_season
            self.recommendation = recommend(
                self.rule, today, self._build_outlook(today), previous, self.settings
            )
            self._last_season = self.recommendation.season
            if self.mounted is None:
                # Assume the car already wears the fitting tires, so nobody is nagged on day one.
                self.mounted = self.recommendation.season.value
            self._publish()

    async def _async_update_forecast(self, today, force: bool) -> None:
        if not self.weather_entity:
            return
        stale = (
            self._forecast_fetched_at is None
            or time.monotonic() - self._forecast_fetched_at >= FORECAST_REFRESH_SECONDS
        )
        if not (force or stale):
            self._forecast = [day for day in self._forecast if day.day >= today]
            return
        forecast = await async_daily_forecast(
            self.hass, self.weather_entity, today, self.settings.forecast_days
        )
        if forecast or force:
            self._forecast = forecast
        # An empty answer is retried at the next evaluation instead of waiting half an hour.
        self._forecast_fetched_at = time.monotonic() if forecast else None

    def _resolve_weather_entity(self) -> bool:
        """Pick the weather entity for an automatic setup; True if the choice changed."""
        if not self._auto_weather:
            return False
        entities = sorted(self.hass.states.async_entity_ids("weather"))
        chosen = entities[0] if entities else None
        if chosen == self.weather_entity:
            return False
        self.weather_entity = chosen
        self._forecast = []
        self._forecast_fetched_at = None
        return True

    def _subscribe_to_states(self) -> None:
        """(Re)subscribe to the entities that feed the evaluation."""
        if self._state_unsubscribe:
            self._state_unsubscribe()
            self._state_unsubscribe = None
        watched = [entity for entity in (self.weather_entity, self.temperature_entity) if entity]
        if watched:
            self._state_unsubscribe = async_track_state_change_event(
                self.hass, watched, self._handle_state_change
            )

    def _current_temperature(self) -> Optional[float]:
        for entity in (self.temperature_entity, self.weather_entity):
            value = read_current_temperature(self.hass, entity)
            if value is not None:
                return value
        return None

    def _record_sample(self, today) -> None:
        current = self._current_temperature()
        if current is not None:
            self._history.add(today, current, is_snowing(self.hass, self.weather_entity))

    def _build_outlook(self, today) -> Optional[Outlook]:
        current = self._current_temperature()
        snow_now = is_snowing(self.hass, self.weather_entity)
        if self._forecast:
            days = list(self._forecast)
            if current is not None and days[0].day == today:
                first = days[0]
                days[0] = DayWeather(
                    today, min(first.minimum, current), max(first.maximum, current), first.snow
                )
            return Outlook(tuple(days), "forecast", snow_now, current)
        recent = self._history.recent(today, self.settings.forecast_days)
        if recent:
            return Outlook(tuple(recent), "history", snow_now, current)
        return None

    # --- reacting to the outside world --------------------------------------------

    @callback
    def _handle_state_change(self, event: Any) -> None:
        self.hass.async_create_task(self.async_refresh())

    @callback
    def _handle_started(self, event: Any) -> None:
        self._started_unsubscribe = None
        self.hass.async_create_task(self.async_refresh())

    @callback
    def _handle_interval(self, now: Any) -> None:
        self.hass.async_create_task(self.async_refresh())

    def _publish(self) -> None:
        """Hand the new state to entities, notifications and storage."""
        self._store.async_delay_save(self._data_to_store, STORAGE_SAVE_DELAY_SECONDS)
        self._update_notification()
        for listener in list(self._listeners):
            listener()

    def _data_to_store(self) -> Dict[str, Any]:
        return {
            "mounted": self.mounted,
            "last_season": self._last_season.value if self._last_season else None,
            "history": self._history.as_dict(),
        }

    # --- persistent notification --------------------------------------------------

    @property
    def _notification_id(self) -> str:
        return f"{DOMAIN}_{self.entry.entry_id}"

    def _update_notification(self) -> None:
        """Show one notification while a tire change is due, and remove it afterwards."""
        target = self.change_target
        if not self.notifications_enabled or target is None:
            if self._notified_for is not None:
                self._dismiss_notification()
            return
        if self._notified_for is target or self.recommendation is None:
            return
        content = build_notification(self._messages, target, self.recommendation.reason)
        persistent_notification.async_create(
            self.hass,
            content["message"],
            title=f"{self.entry.title}: {content['title']}",
            notification_id=self._notification_id,
        )
        self._notified_for = target

    def _dismiss_notification(self) -> None:
        persistent_notification.async_dismiss(self.hass, self._notification_id)
        self._notified_for = None
