"""Every translation is complete, and backed by a checked country."""
import json
import re
import unittest
from pathlib import Path

from support import COMPONENT, load

engine = load("engine")
languages = load("languages")
messages = load("messages")

TRANSLATIONS = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in (COMPONENT / "translations").glob("*.json")}
MESSAGES = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in (COMPONENT / "messages").glob("*.json")}


def key_paths(node, prefix=""):
    """All leaf paths of a nested dictionary."""
    if isinstance(node, dict):
        return {path for key, value in node.items() for path in key_paths(value, f"{prefix}{key}.")}
    return {prefix.rstrip(".")}


def leaves(node):
    if isinstance(node, dict):
        return [leaf for value in node.values() for leaf in leaves(value)]
    return [node]


class Translations(unittest.TestCase):
    def test_every_language_is_listed_with_its_countries(self):
        self.assertEqual(set(TRANSLATIONS), set(languages.LANGUAGE_COUNTRIES))
        self.assertEqual(set(MESSAGES), set(languages.LANGUAGE_COUNTRIES))

    def test_strings_json_is_the_english_source(self):
        self.assertEqual(json.loads((COMPONENT / "strings.json").read_text(encoding="utf-8")), TRANSLATIONS["en"])

    def test_every_translation_has_the_keys_of_english(self):
        reference = key_paths(TRANSLATIONS["en"])
        for language, content in TRANSLATIONS.items():
            self.assertEqual(key_paths(content), reference, language)

    def test_every_message_file_has_the_keys_of_english(self):
        reference = key_paths(MESSAGES["en"])
        for language, content in MESSAGES.items():
            self.assertEqual(key_paths(content), reference, language)

    def test_no_empty_or_untranslated_placeholder_text(self):
        for language, content in {**{f"t:{k}": v for k, v in TRANSLATIONS.items()}, **{f"m:{k}": v for k, v in MESSAGES.items()}}.items():
            for text in leaves(content):
                self.assertTrue(text.strip(), language)
                self.assertNotIn("{", text, language)

    def test_non_latin_languages_are_really_translated(self):
        scripts = {"ru": r"[Ѐ-ӿ]", "uk": r"[Ѐ-ӿ]", "bg": r"[Ѐ-ӿ]", "mk": r"[Ѐ-ӿ]", "sr": r"[Ѐ-ӿ]",
                   "el": r"[Ͱ-Ͽ]", "ja": r"[぀-ヿ一-鿿]", "ko": r"[가-힣]",
                   "zh-Hans": r"[一-鿿]", "zh-Hant": r"[一-鿿]"}
        for language, pattern in scripts.items():
            for text in leaves(MESSAGES[language]):
                self.assertRegex(text, pattern, f"{language}: {text}")

    def test_other_languages_differ_from_english(self):
        english = MESSAGES["en"]["to_winter"]
        for language, content in MESSAGES.items():
            if language != "en":
                self.assertNotEqual(content["to_winter"], english, language)

    def test_messages_cover_every_reason(self):
        for language, content in MESSAGES.items():
            self.assertEqual(set(content["reasons"]), {reason.value for reason in engine.Reason}, language)

    def test_translated_state_names_exist_for_every_season(self):
        for language, content in TRANSLATIONS.items():
            states = content["entity"]["sensor"]["recommendation"]["state"]
            self.assertEqual(set(states), {season.value for season in engine.Season}, language)


class MessageLoading(unittest.TestCase):
    def test_language_candidates(self):
        self.assertEqual(messages.language_candidates("pt-BR"), ["pt-BR", "pt"])
        self.assertEqual(messages.language_candidates("no"), ["nb"])
        self.assertEqual(messages.language_candidates("zh-TW"), ["zh-hant", "zh"])
        self.assertEqual(messages.language_candidates("de"), ["de"])

    def test_loading_falls_back_to_english(self):
        english = messages.load_messages("en")
        self.assertEqual(messages.load_messages("xx"), english)
        self.assertEqual(messages.load_messages("pt-BR")["title"], MESSAGES["pt"]["title"])
        self.assertEqual(messages.load_messages("sr-Latn")["title"], MESSAGES["sr-Latn"]["title"])

    def test_notification_text(self):
        text = messages.build_notification(messages.load_messages("de"), engine.Season.WINTER, engine.Reason.FROST_RISK)
        self.assertEqual(text["title"], MESSAGES["de"]["title"])
        self.assertIn(MESSAGES["de"]["to_winter"], text["message"])
        self.assertIn(MESSAGES["de"]["reasons"]["frost_risk"], text["message"])


if __name__ == "__main__":
    unittest.main()
