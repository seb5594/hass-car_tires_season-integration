"""Constants for the Car Tires Season integration."""
from __future__ import annotations

DOMAIN = "car_tires_season"
DEFAULT_NAME = "Car Tires Season"

PLATFORMS = ["sensor", "binary_sensor", "select"]

# Configuration keys (stored in the config entry, options override the data).
CONF_COUNTRY = "country"
CONF_REGION = "region"
CONF_WEATHER_ENTITY = "weather_entity"
CONF_TEMPERATURE_ENTITY = "temperature_entity"
CONF_THRESHOLD = "temperature_threshold"
CONF_FORECAST_DAYS = "forecast_days"
CONF_NOTIFICATIONS = "notifications"
# Set by the automatic setup: use the first weather entity Home Assistant has.
CONF_AUTO_WEATHER = "auto_weather"
# Marks an entry that was created by self-discovery, without any user input.
CONF_AUTO_DISCOVERED = "auto_discovered"

# Values of the "mounted tires" select besides the two seasons.
ALL_SEASON = "all_season"

# How often the weather forecast is fetched at most, in seconds.
FORECAST_REFRESH_SECONDS = 30 * 60
# The periodic re-evaluation (it also notices the date change), in seconds.
EVALUATION_INTERVAL_SECONDS = 30 * 60

STORAGE_VERSION = 1
STORAGE_SAVE_DELAY_SECONDS = 600
