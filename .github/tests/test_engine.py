"""The recommendation logic."""
import unittest
from datetime import date, timedelta

from support import load

engine = load("engine")
rules_data = load("rules_data")
rules = load("rules")

Season, Reason, LegalStatus = engine.Season, engine.Reason, engine.LegalStatus
DayWeather, Outlook, Settings = engine.DayWeather, engine.Outlook, engine.Settings


def outlook(start, lows_highs, source="forecast", **kwargs):
    days = tuple(DayWeather(start + timedelta(days=i), low, high) for i, (low, high) in enumerate(lows_highs))
    return Outlook(days, source, **kwargs)


def decide(country, day, weather=None, previous=None, region=None):
    rule = rules_data.rule_for(country, region, False)
    return engine.recommend(rule, day, weather, previous, Settings())


class LegalPeriods(unittest.TestCase):
    def test_russia_requires_winter_tires_from_december_to_february(self):
        for day in (date(2026, 12, 1), date(2027, 1, 15), date(2027, 2, 28), date(2028, 2, 29)):
            result = decide("RU", day, outlook(day, [(10, 20)] * 3))
            self.assertEqual((result.season, result.reason), (Season.WINTER, Reason.LEGAL_PERIOD), day)
            self.assertEqual(result.legal_status, LegalStatus.REQUIRED)

    def test_russia_in_summer_ignores_a_cold_night(self):
        day = date(2027, 7, 10)
        result = decide("RU", day, outlook(day, [(-3, 8)] * 3))
        self.assertEqual((result.season, result.reason), (Season.SUMMER, Reason.OUTSIDE_SEASON))

    def test_legal_period_wins_over_warm_weather(self):
        day = date(2026, 12, 20)
        self.assertEqual(decide("LV", day, outlook(day, [(14, 22)] * 3)).season, Season.WINTER)

    def test_conditional_obligation_does_not_force_winter(self):
        day = date(2026, 11, 5)
        result = decide("AT", day, outlook(day, [(9, 17)] * 5))
        self.assertEqual(result.season, Season.SUMMER)
        self.assertEqual(result.legal_status, LegalStatus.CONDITIONAL)

    def test_snow_now_makes_a_conditional_duty_required(self):
        day = date(2026, 12, 5)
        result = decide("DE", day, outlook(day, [(-1, 1)] * 3, snow_now=True))
        self.assertEqual(result.legal_status, LegalStatus.REQUIRED)
        self.assertEqual((result.season, result.reason), (Season.WINTER, Reason.SNOW_EXPECTED))

    def test_regional_rule_is_reported_as_regional(self):
        day = date(2026, 12, 5)
        self.assertEqual(decide("FR", day).legal_status, LegalStatus.REGIONAL)

    def test_no_duty_country(self):
        self.assertEqual(decide("GB", date(2026, 12, 5)).legal_status, LegalStatus.NOT_REQUIRED)

    def test_canadian_regions(self):
        day = date(2027, 1, 20)
        self.assertEqual(decide("CA", day, region="QC").legal_status, LegalStatus.REQUIRED)
        self.assertEqual(decide("CA", day, region="QC").season, Season.WINTER)
        self.assertEqual(decide("CA", day).legal_status, LegalStatus.NOT_REQUIRED)


class WeatherDecisions(unittest.TestCase):
    def test_cold_week_in_autumn_recommends_winter(self):
        day = date(2026, 11, 3)
        result = decide("DE", day, outlook(day, [(3, 6)] * 5))
        self.assertEqual((result.season, result.reason), (Season.WINTER, Reason.COLD_WEATHER))

    def test_frost_alone_recommends_winter(self):
        day = date(2026, 10, 20)
        result = decide("DE", day, outlook(day, [(-1, 12)] + [(5, 14)] * 4))
        self.assertEqual((result.season, result.reason), (Season.WINTER, Reason.FROST_RISK))

    def test_mild_autumn_keeps_summer_tires(self):
        day = date(2026, 10, 10)
        result = decide("DE", day, outlook(day, [(8, 16)] * 5))
        self.assertEqual((result.season, result.reason), (Season.SUMMER, Reason.MILD_WEATHER))

    def test_forecast_snow_recommends_winter(self):
        day = date(2026, 11, 10)
        weather = Outlook((DayWeather(day, 4, 9, snow=True),) + (DayWeather(day + timedelta(days=1), 8, 12),), "forecast")
        self.assertEqual(decide("DE", day, weather).reason, Reason.SNOW_EXPECTED)

    def test_spring_release_needs_a_clear_margin(self):
        day = date(2027, 4, 2)
        borderline = outlook(day, [(2, 9)] * 5)  # mean 5.5 °C, frost-free
        self.assertEqual(decide("DE", day, borderline, previous=Season.WINTER).season, Season.WINTER)
        warm = outlook(day, [(6, 17)] * 5)  # mean 11.5 °C
        self.assertEqual(decide("DE", day, warm, previous=Season.WINTER).season, Season.SUMMER)

    def test_hysteresis_band_around_the_threshold(self):
        day = date(2026, 11, 2)
        band = outlook(day, [(5, 10.5)] * 5)  # mean 7.75 °C: between 7 and 8
        self.assertEqual(decide("DE", day, band, previous=Season.SUMMER).season, Season.SUMMER)
        self.assertEqual(decide("DE", day, band, previous=Season.WINTER).season, Season.WINTER)

    def test_weather_is_ignored_far_from_the_winter_season(self):
        day = date(2026, 7, 15)
        self.assertEqual(decide("DE", day, outlook(day, [(-2, 5)] * 3)).reason, Reason.OUTSIDE_SEASON)

    def test_custom_threshold(self):
        day = date(2026, 10, 20)
        rule = rules_data.rule_for("DE", None, False)
        weather = outlook(day, [(7, 11)] * 5)  # mean 9 °C
        self.assertEqual(engine.recommend(rule, day, weather, None, Settings(temperature_threshold=7)).season, Season.SUMMER)
        self.assertEqual(engine.recommend(rule, day, weather, None, Settings(temperature_threshold=10)).season, Season.WINTER)


class CalendarFallback(unittest.TestCase):
    def test_germany_between_october_and_easter(self):
        self.assertEqual(decide("DE", date(2026, 10, 1)).reason, Reason.SEASON_CALENDAR)
        self.assertEqual(decide("DE", date(2027, 3, 20)).season, Season.WINTER)
        self.assertEqual(decide("DE", date(2027, 4, 1)).season, Season.SUMMER)

    def test_unknown_country_uses_the_generic_season_of_its_hemisphere(self):
        north = engine.recommend(rules_data.rule_for("XX", None, False), date(2026, 12, 24), None, None, Settings())
        south = engine.recommend(rules_data.rule_for("XX", None, True), date(2026, 12, 24), None, None, Settings())
        self.assertEqual(north.season, Season.WINTER)
        self.assertEqual(south.season, Season.SUMMER)
        self.assertEqual(rules_data.rule_for("XX", None, True).confidence, "none")


class History(unittest.TestCase):
    def test_readings_become_daily_extremes(self):
        history = engine.TemperatureHistory()
        today = date(2026, 11, 10)
        for temperature in (4.0, 9.5, 1.0):
            history.add(today, temperature)
        history.add(today - timedelta(days=1), 6.0, snow=True)
        recent = history.recent(today, 3)
        self.assertEqual([(d.day, d.minimum, d.maximum, d.snow) for d in recent],
                         [(date(2026, 11, 9), 6.0, 6.0, True), (today, 1.0, 9.5, False)])

    def test_round_trip_and_damaged_data(self):
        history = engine.TemperatureHistory()
        history.add(date(2026, 11, 10), 3.0)
        restored = engine.TemperatureHistory.from_dict(history.as_dict())
        self.assertEqual(restored.as_dict(), history.as_dict())
        self.assertEqual(engine.TemperatureHistory.from_dict({"nonsense": 1, "2026-01-01": ["x"]}).as_dict(), {})

    def test_old_days_are_dropped(self):
        history = engine.TemperatureHistory(keep_days=5)
        history.add(date(2026, 11, 1), 3.0)
        history.add(date(2026, 11, 20), 3.0)
        self.assertEqual(list(history.as_dict()), ["2026-11-20"])


if __name__ == "__main__":
    unittest.main()
