"""Integrity of the researched country rules."""
import re
import unittest
from datetime import date

from support import load

rules_data = load("rules_data")
rules = load("rules")
languages = load("languages")
names = load("country_names").COUNTRY_NAMES
timezones = load("timezones")

ALL_RULES = list(rules_data.RULES.values())
EVERY_RULE = ALL_RULES + [variant for rule in ALL_RULES for variant in rule.regions.values()]


class RuleData(unittest.TestCase):
    def test_every_rule_names_its_country_and_sources(self):
        for rule in EVERY_RULE:
            self.assertRegex(rule.country, r"^[A-Z]{2}$")
            self.assertIn(rule.confidence, {"high", "medium", "low"}, rule.country)
            self.assertTrue(rule.sources, f"{rule.country} has no source")
            for url in rule.sources:
                self.assertRegex(url, r"^https://", rule.country)
            date.fromisoformat(rule.checked)

    def test_dictionary_keys_match_the_countries(self):
        for code, rule in rules_data.RULES.items():
            self.assertEqual(code, rule.country)
            for variant in rule.regions.values():
                self.assertEqual(variant.country, code)

    def test_every_country_has_an_english_name(self):
        self.assertEqual(set(names), set(rules_data.RULES))

    def test_windows_are_plausible_for_every_year(self):
        for rule in EVERY_RULE:
            for year in range(2020, 2045):
                start, end = rule.window.span_starting_in(year)
                length = (end - start).days
                self.assertTrue(60 <= length <= 300, f"{rule.country} {year}: {length} days")

    def test_period_rules_have_no_practical_filler(self):
        # A legal period must come from a source, never from the generic default.
        for rule in EVERY_RULE:
            if rule.has_legal_period:
                self.assertIsNot(rule.window, rules.NORTHERN_DEFAULT_WINDOW, rule.country)

    def test_regional_variants_only_exist_where_declared(self):
        self.assertEqual({c for c, r in rules_data.RULES.items() if r.regions}, {"CA"})

    def test_spot_checks_against_the_researched_sources(self):
        rule = rules_data.RULES
        self.assertEqual(rule["DE"].obligation, rules.Obligation.CONDITIONS)
        self.assertEqual(rule["RU"].window.span_starting_in(2026), (date(2026, 12, 1), date(2027, 2, 28)))
        self.assertEqual(rule["LT"].window.span_starting_in(2026), (date(2026, 11, 10), date(2027, 3, 31)))
        self.assertEqual(rule["SE"].window.span_starting_in(2026), (date(2026, 12, 1), date(2027, 3, 31)))
        self.assertEqual(rule["CA"].regions["QC"].window.span_starting_in(2026), (date(2026, 12, 1), date(2027, 3, 15)))
        self.assertEqual(rule["DE"].window.span_starting_in(2026), (date(2026, 10, 1), date(2027, 3, 28)))

    def test_lookup_falls_back_to_a_generic_rule(self):
        generic = rules_data.rule_for("zz", None, False)
        self.assertEqual((generic.country, generic.obligation, generic.confidence), ("ZZ", rules.Obligation.NONE, "none"))
        self.assertEqual(rules_data.rule_for("de", None, False).country, "DE")
        self.assertEqual(rules_data.rule_for("CA", "QC", False).obligation, rules.Obligation.SEASON)
        self.assertEqual(rules_data.rule_for("CA", "unknown", False), rules_data.RULES["CA"])


class TimeZones(unittest.TestCase):
    def test_only_researched_countries_are_mapped(self):
        for zone, code in timezones.TIME_ZONE_COUNTRIES.items():
            self.assertIn(code, rules_data.RULES, zone)
            self.assertRegex(zone, r"^[A-Za-z_]+/[A-Za-z_]+$")

    def test_lookup(self):
        self.assertEqual(timezones.country_from_time_zone("Europe/Berlin"), "DE")
        self.assertEqual(timezones.country_from_time_zone("Europe/Moscow"), "RU")
        self.assertIsNone(timezones.country_from_time_zone("UTC"))
        self.assertIsNone(timezones.country_from_time_zone(None))


class LanguageCoverage(unittest.TestCase):
    def test_every_language_is_backed_by_a_checked_country(self):
        for language, countries in languages.LANGUAGE_COUNTRIES.items():
            self.assertTrue(countries, language)
            for country in countries:
                self.assertIn(country, rules_data.RULES, f"{language}: no rule for {country}")
                self.assertTrue(rules_data.RULES[country].is_researched, f"{language}/{country}")
                self.assertRegex(rules_data.RULES[country].checked, re.compile(r"^\d{4}-\d{2}-\d{2}$"))

    def test_every_language_has_at_least_one_country_with_solid_evidence(self):
        weak = {"CN", "KR"}  # Only weak sources were found; listed openly in docs/COUNTRY_RULES.md.
        for language, countries in languages.LANGUAGE_COUNTRIES.items():
            solid = [c for c in countries if rules_data.RULES[c].confidence in {"high", "medium"}]
            self.assertTrue(solid or set(countries) <= weak, language)


if __name__ == "__main__":
    unittest.main()
