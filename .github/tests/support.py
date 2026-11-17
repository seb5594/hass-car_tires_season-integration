"""Load the integration's Home-Assistant-free modules without importing its package."""
import importlib
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COMPONENT = ROOT / "custom_components" / "car_tires_season"
PACKAGE = "car_tires_season_pure"


def load(module):
    """Import a module of the component under a stub package, so `__init__.py` never runs."""
    if PACKAGE not in sys.modules:
        stub = types.ModuleType(PACKAGE)
        stub.__path__ = [str(COMPONENT)]
        sys.modules[PACKAGE] = stub
    return importlib.import_module(f"{PACKAGE}.{module}")
