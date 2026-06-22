"""Build the JSON payload the configurable planner uses in the browser.

All registry resolution (purchase_as, display names, grocery category, skip,
purchase notes) and unit->base conversion happen *here*, in Python, so the
browser never re-implements them. Each recipe ingredient is emitted as an
already-resolved grocery contribution: display, category, note, and either a
canonical (base, dim) pair or a "taste" flag.
"""
import json

from . import data, units
from .grocery import CATEGORY_ORDER

# Which recipe categories can fill each editable meal-plan slot.
SLOT_CATEGORIES = {
    "protein": ("protein-anchor", "binder"),
    "cooked_veg": ("side",),
    "salad": ("salad",),
}


def _ings(recipe, reg):
    out = []
    for ig in recipe["ingredients"]:
        entry = reg.get(ig["item"], {})
        cat = entry.get("grocery_category", "pantry-spice")
        if cat == "skip":
            continue
        buy_id = entry.get("purchase_as", ig["item"])
        buy_entry = reg.get(buy_id, entry)
        display = buy_entry.get("display", buy_id)
        note = entry.get("purchase_note", "") or ""
        qty, unit = ig.get("qty"), ig.get("unit")
        if qty is None or unit in ("to_taste", "as_needed", "to_cover"):
            out.append({"d": display, "c": cat, "note": note, "taste": 1})
        else:
            dim, val = units.to_base(qty, unit)
            out.append({"d": display, "c": cat, "note": note,
                        "b": round(val, 4), "dim": dim})
    return out


def payload():
    recipes = data.recipes()
    reg = data.registry()

    rec = {}
    for rid, r in recipes.items():
        rec[rid] = {
            "name": r["name"],
            "category": r["category"],
            "batch": bool(r.get("batch", False)),
            "ings": _ings(r, reg),
        }

    options = {}
    for slot, cats in SLOT_CATEGORIES.items():
        opts = [[rid, recipes[rid]["name"]] for rid in recipes
                if recipes[rid]["category"] in cats]
        opts.sort(key=lambda x: x[1])
        options[slot] = opts

    default_plan = []
    for d in data.meal_plan().get("days", []):
        default_plan.append({
            "day": d["day"],
            "protein": d.get("protein", ""),
            "cooked_veg": d.get("cooked_veg", ""),
            "salad": d.get("salad", ""),
            "extras": list(d.get("extras", [])),
        })

    return {
        "categories": [list(c) for c in CATEGORY_ORDER],
        "recipes": rec,
        "options": options,
        "defaultPlan": default_plan,
    }


def to_json():
    return json.dumps(payload(), ensure_ascii=False, separators=(",", ":"))
