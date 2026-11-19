"""Static checks that need no Home Assistant installation."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COMPONENT = next((ROOT / "custom_components").iterdir())


class IntegrationLayout(unittest.TestCase):
    def test_manifest_domain_matches_folder_and_constants(self):
        manifest = json.loads((COMPONENT / "manifest.json").read_text())
        self.assertEqual(manifest["domain"], COMPONENT.name)
        self.assertIn(f'DOMAIN = "{COMPONENT.name}"', (COMPONENT / "const.py").read_text())

    def test_version_follows_the_calendar_scheme(self):
        manifest = json.loads((COMPONENT / "manifest.json").read_text())
        # First build of a day: YYYY.MM.DD, every further one gets .1, .2 and so on.
        self.assertRegex(manifest["version"], r"^20\d\d\.(?:[1-9]|1[0-2])\.(?:[1-9]|[12]\d|3[01])(?:\.[1-9]\d*)?$")

    def test_hacs_archive_matches_the_domain(self):
        hacs = json.loads((ROOT / "hacs.json").read_text())
        self.assertEqual(hacs["filename"], f"{COMPONENT.name}.zip")

    def test_categories_are_one_to_three_distinct_entries(self):
        manifest = json.loads((COMPONENT / "manifest.json").read_text())
        categories = manifest["categories"]
        self.assertTrue(1 <= len(categories) <= 3)
        self.assertEqual(len(set(categories)), len(categories))
        self.assertEqual(categories[0], "vehicles_transport.cars_evs")

    def test_manifest_keys_are_sorted_like_hassfest_wants(self):
        keys = list(json.loads((COMPONENT / "manifest.json").read_text()))
        self.assertEqual(keys[:2], ["domain", "name"])
        self.assertEqual(keys[2:], sorted(keys[2:]))

    def test_self_discovery_is_declared(self):
        manifest = json.loads((COMPONENT / "manifest.json").read_text())
        self.assertIn("_home-assistant._tcp.local.", manifest["zeroconf"])

    def test_no_python_310_only_syntax(self):
        # Home Assistant 2022.4 still runs Python 3.9.
        import ast
        for path in COMPONENT.glob("*.py"):
            ast.parse(path.read_text(), filename=str(path), feature_version=(3, 9))
            self.assertIn("from __future__ import annotations", path.read_text(), path.name)

    def test_brand_images_exist(self):
        for name in ("icon.png", "icon@2x.png"):
            self.assertTrue((COMPONENT / "brand" / name).is_file(), name)

    def test_country_documentation_is_current(self):
        import subprocess
        import sys
        result = subprocess.run([sys.executable, str(ROOT / ".github/checks/country_rules_doc.py")],
                                capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(result.returncode, 0, result.stdout)


if __name__ == "__main__":
    unittest.main()
