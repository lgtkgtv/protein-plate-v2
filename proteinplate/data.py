"""Data access for the ProteinPlate content layer.

Locates the data/ directory relative to this package, so it works whether
called from the website build (mkdocs), the CLI, or a test — no cwd assumptions.
"""
import os
import functools
import yaml

_PKG_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(_PKG_DIR)
DATA_DIR = os.path.join(ROOT, "data")
RECIPE_DIR = os.path.join(DATA_DIR, "recipes")
ING_FILE = os.path.join(DATA_DIR, "ingredients.yaml")
PLAN_FILE = os.path.join(DATA_DIR, "meal_plan.yaml")


def _load(path):
    with open(path) as f:
        return yaml.safe_load(f)


@functools.lru_cache(maxsize=1)
def registry():
    """id -> {display, grocery_category, ...}"""
    return _load(ING_FILE)


@functools.lru_cache(maxsize=1)
def recipes():
    """id -> recipe dict, sorted by id."""
    out = {}
    for fname in sorted(os.listdir(RECIPE_DIR)):
        if fname.endswith(".yaml"):
            r = _load(os.path.join(RECIPE_DIR, fname))
            out[r["id"]] = r
    return out


@functools.lru_cache(maxsize=1)
def meal_plan():
    return _load(PLAN_FILE)


def display_name(item_id):
    return registry().get(item_id, {}).get("display", item_id)
