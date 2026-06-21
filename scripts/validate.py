#!/usr/bin/env python3
"""
Validate every recipe in data/recipes/ against schema/recipe.schema.json,
plus checks that JSON Schema alone cannot express:

  1. recipe `id` matches its filename
  2. every ingredient `item` resolves to an id in data/ingredients.yaml
  3. every registry `grocery_category` is one of the allowed values
  4. protein anchors declare a `protein_family`

Exit code is non-zero if anything fails, so this drops straight into CI.

Usage:  uv run python scripts/validate.py
"""
import json
import os
import sys
import yaml
from jsonschema import Draft202012Validator

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RECIPE_DIR = os.path.join(ROOT, "data", "recipes")
ING_FILE = os.path.join(ROOT, "data", "ingredients.yaml")
SCHEMA_FILE = os.path.join(ROOT, "schema", "recipe.schema.json")

ALLOWED_GROCERY_CATEGORIES = {
    "produce", "protein-dairy", "nuts-seeds", "flour",
    "fat-oil", "pantry-spice", "condiment-other", "skip",
}


def load_yaml(path):
    with open(path) as f:
        return yaml.safe_load(f)


def main():
    errors = []

    # --- registry --------------------------------------------------------
    registry = load_yaml(ING_FILE)
    for iid, entry in registry.items():
        cat = entry.get("grocery_category")
        if cat not in ALLOWED_GROCERY_CATEGORIES:
            errors.append(f"[ingredients.yaml] '{iid}': bad grocery_category '{cat}'")
    known_ingredients = set(registry.keys())

    # --- schema ----------------------------------------------------------
    with open(SCHEMA_FILE) as f:
        schema = json.load(f)
    validator = Draft202012Validator(schema)

    files = sorted(f for f in os.listdir(RECIPE_DIR) if f.endswith(".yaml"))
    for fname in files:
        path = os.path.join(RECIPE_DIR, fname)
        recipe = load_yaml(path)
        rid = recipe.get("id", "?")

        # 1. schema
        for e in sorted(validator.iter_errors(recipe), key=lambda e: e.path):
            loc = "/".join(str(p) for p in e.path) or "(root)"
            errors.append(f"[{fname}] schema @ {loc}: {e.message}")

        # 2. id == filename
        if rid != fname[:-5]:
            errors.append(f"[{fname}] id '{rid}' does not match filename")

        # 3. ingredient references resolve
        for ig in recipe.get("ingredients", []):
            item = ig.get("item")
            if item not in known_ingredients:
                errors.append(f"[{fname}] unknown ingredient '{item}' "
                              f"(add it to data/ingredients.yaml)")

        # 4. protein anchors should declare a family
        if recipe.get("category") == "protein-anchor" and not recipe.get("protein_family"):
            errors.append(f"[{fname}] protein-anchor is missing protein_family")

    # --- meal plan references --------------------------------------------
    plan_file = os.path.join(ROOT, "data", "meal_plan.yaml")
    known_recipes = {f[:-5] for f in files}
    if os.path.exists(plan_file):
        plan = load_yaml(plan_file)
        refs = set(plan.get("batches", {}).keys())
        for day in plan.get("days", []):
            for key in ("protein", "cooked_veg", "salad"):
                if day.get(key):
                    refs.add(day[key])
            refs.update(day.get("extras", []))
        for rid in sorted(refs):
            if rid not in known_recipes:
                errors.append(f"[meal_plan.yaml] references unknown recipe '{rid}'")

    # --- report ----------------------------------------------------------
    print(f"Checked {len(files)} recipes against {len(known_ingredients)} known ingredients.")
    if errors:
        print(f"\nFAILED with {len(errors)} problem(s):")
        for e in errors:
            print("  - " + e)
        sys.exit(1)
    print("All recipes valid.")


if __name__ == "__main__":
    main()
