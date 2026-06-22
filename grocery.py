"""Grocery aggregation: a plan (recipe -> batches) becomes a categorised list.

Pure logic, no I/O of its own beyond reading the data layer. The website
generator and the CLI both call aggregate() so the shopping list can never
disagree between surfaces. Quantities are unit-normalized (see units.py) so each
ingredient appears as one tidy amount instead of one line per unit.
"""
from . import data
from . import units

CATEGORY_ORDER = [
    ("produce", "Vegetables, fruit & herbs"),
    ("protein-dairy", "Proteins & dairy"),
    ("nuts-seeds", "Nuts & seeds"),
    ("flour", "Flours & dals"),
    ("fat-oil", "Fats & oils"),
    ("pantry-spice", "Pantry & spices"),
    ("condiment-other", "Condiments / other"),
]


def aggregate(plan):
    """plan: dict or list of (recipe_id, batches).

    Returns (totals, to_taste, notes):
      totals   : list of {category, display, amounts} where amounts is a list of
                 (qty, unit) display tuples, normalized per dimension and sorted.
      to_taste : {category: [display, ...]} for null / "as needed" items
      notes    : {display: purchase_note}
    """
    if isinstance(plan, dict):
        plan = list(plan.items())

    reg = data.registry()
    recipes = data.recipes()

    # (category, display) -> list of (qty, unit) raw contributions
    raw = {}
    cat_of = {}
    to_taste = {}      # category -> set(display)
    notes = {}

    for rid, batches in plan:
        recipe = recipes[rid]
        for ig in recipe["ingredients"]:
            entry = reg.get(ig["item"], {})
            cat = entry.get("grocery_category", "pantry-spice")
            if cat == "skip":
                continue
            buy_id = entry.get("purchase_as", ig["item"])
            buy_entry = reg.get(buy_id, entry)
            display = buy_entry.get("display", buy_id)
            if entry.get("purchase_note"):
                notes[display] = entry["purchase_note"]

            qty, unit = ig.get("qty"), ig.get("unit")
            if qty is None or unit in ("to_taste", "as_needed", "to_cover"):
                to_taste.setdefault(cat, set()).add(display)
                continue
            key = (cat, display)
            cat_of[display] = cat
            raw.setdefault(key, []).append((qty * batches, unit))

    totals = []
    for (cat, display), amounts in raw.items():
        totals.append({
            "category": cat,
            "display": display,
            "amounts": units.normalize(amounts),
        })
    totals.sort(key=lambda r: (r["category"], r["display"]))
    to_taste = {c: sorted(v) for c, v in to_taste.items()}
    return totals, to_taste, notes
