"""Render data-layer content into Markdown pages.

Every function returns a Markdown string. The mkdocs build (docs/gen_pages.py)
and the local preview script both call these, so the website and any other
surface render from identical logic.
"""
from . import data
from .grocery import aggregate, CATEGORY_ORDER

# Category -> section heading on the recipes page, in display order.
RECIPE_SECTIONS = [
    ("protein-anchor", "Protein anchors"),
    ("binder", "The binder"),
    ("side", "Daily sides"),
    ("salad", "Salads (no/low cooking)"),
    ("condiment", "Condiments & extras"),
]

_FRACTIONS = {0.25: "¼", 0.5: "½", 0.75: "¾", 0.33: "⅓", 0.67: "⅔"}


def _num(q):
    if q is None:
        return ""
    whole, frac = divmod(round(q, 2), 1)
    frac = round(frac, 2)
    if frac in _FRACTIONS:
        return (f"{int(whole)}" if whole else "") + _FRACTIONS[frac]
    return str(int(q)) if abs(q - round(q)) < 1e-9 else f"{q:g}"


def _ingredient(ig):
    item = ig["item"]
    name = data.display_name(item)
    prep = f" ({ig['prep']})" if ig.get("prep") else ""
    opt = " *(optional)*" if ig.get("optional") else ""
    qty, unit = ig.get("qty"), ig.get("unit")
    if qty is None or unit in ("to_taste", "as_needed", "to_cover"):
        word = {"to_taste": "to taste", "as_needed": "as needed",
                "to_cover": "to cover"}.get(unit, "as needed")
        return f"{name} {word}{prep}{opt}"
    if unit == "piece":
        return f"{_num(qty)} {name}{prep}{opt}"
    return f"{_num(qty)} {unit} {name}{prep}{opt}"


def _storage_line(storage):
    if not storage:
        return ""
    def days(n):
        return f"{n} day" if n == 1 else f"{n} days"
    bits = []
    if storage.get("fridge_days"):
        bits.append(f"Fridge {days(storage['fridge_days'])}")
    if storage.get("freezer_days"):
        bits.append(f"Freeze {days(storage['freezer_days'])}")
    if storage.get("note"):
        bits.append(storage["note"])
    return " · ".join(bits)


# --------------------------------------------------------------------------
# Recipes page
# --------------------------------------------------------------------------
def render_recipes_page():
    recipes = data.recipes()
    out = ["# Recipes", "",
           "Every recipe is scaled for a **family of 4** and generated from the "
           "[recipe data](https://github.com/lgtkgtv/protein-plate-v2/tree/main/data). "
           "Pick one protein anchor, then add a cooked veg, a salad, dairy and "
           "nuts/seeds.", ""]
    by_cat = {}
    for r in recipes.values():
        by_cat.setdefault(r["category"], []).append(r)

    for cat, heading in RECIPE_SECTIONS:
        items = sorted(by_cat.get(cat, []), key=lambda r: r["name"])
        if not items:
            continue
        out.append(f"## {heading}\n")
        for r in items:
            out.append(f"### {r['name']}\n")
            img = r.get("media", {}).get("image")
            if img:
                out.append(f"![{r['name']}]({img})\n")
            ings = " · ".join(_ingredient(i) for i in r["ingredients"])
            out.append(f"**Ingredients ({r['base_servings']}):** {ings}\n")
            for n, step in enumerate(r["steps"], 1):
                out.append(f"{n}. {step}")
            out.append("")
            footer = []
            if r.get("media", {}).get("video"):
                footer.append(f"🎥 [video]({r['media']['video']})")
            sl = _storage_line(r.get("storage"))
            if sl:
                footer.append(f"🧊 {sl}")
            for tip in r.get("tips", []):
                footer.append(f"💡 {tip}")
            if footer:
                out.append(" · ".join(footer))
            out.append("")
    return "\n".join(out)


# --------------------------------------------------------------------------
# Ingredients & portions page
# --------------------------------------------------------------------------
def render_ingredients_page():
    recipes = data.recipes()
    out = ["# Ingredients & Portions", "",
           "Each dish mapped to its raw ingredients, then a summary of which "
           "ingredients recur most across the menu. Auto-generated from the data.", ""]

    by_cat = {}
    for r in recipes.values():
        by_cat.setdefault(r["category"], []).append(r)

    for cat, heading in RECIPE_SECTIONS:
        items = sorted(by_cat.get(cat, []), key=lambda r: r["name"])
        if not items:
            continue
        out.append(f"## {heading}\n")
        for r in items:
            ings = " · ".join(_ingredient(i) for i in r["ingredients"])
            out.append(f"- **{r['name']}** — {ings}")
        out.append("")

    # recurring-ingredient summary
    counts = {}
    for r in recipes.values():
        for ig in r["ingredients"]:
            counts[ig["item"]] = counts.get(ig["item"], 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], data.display_name(kv[0])))
    out.append("## Recurring ingredients\n")
    out.append("How many recipes use each ingredient — your highest-leverage staples.\n")
    out.append("| Ingredient | Used in (recipes) |")
    out.append("| --- | --- |")
    for item, n in ranked:
        if n >= 3:
            out.append(f"| {data.display_name(item)} | {n} |")
    out.append("")
    return "\n".join(out)


# --------------------------------------------------------------------------
# Grocery list page
# --------------------------------------------------------------------------
def render_grocery_page():
    plan = data.meal_plan().get("batches", {})
    totals, to_taste, notes = aggregate(plan)
    out = ["# Grocery List", "",
           "Generated from the [7-day meal plan](meal-plan.md) — one week, "
           "family of 4. Tick items off as you shop.", ""]
    for cat, heading in CATEGORY_ORDER:
        rows = [t for t in totals if t["category"] == cat]
        extras = [d for d in to_taste.get(cat, [])
                  if not any(t["display"] == d for t in rows)]
        if not rows and not extras:
            continue
        out.append(f"## {heading}\n")
        for t in rows:
            note = f"  *({notes[t['display']]})*" if t["display"] in notes else ""
            out.append(f"- [ ] {t['display']} — {_num(t['qty'])} {t['unit']}{note}")
        for d in extras:
            note = f"  *({notes[d]})*" if d in notes else ""
            out.append(f"- [ ] {d} — to taste / as needed{note}")
        out.append("")
    return "\n".join(out)


# --------------------------------------------------------------------------
# 7-day meal plan page
# --------------------------------------------------------------------------
def render_meal_plan_page():
    recipes = data.recipes()
    plan = data.meal_plan()

    def name(rid):
        return recipes[rid]["name"] if rid in recipes else rid

    out = ["# 7-Day Meal Plan", "",
           f"A decision-free week for a family of {plan.get('servings', 4)}. "
           "Each plate = a protein anchor + a cooked veg + a salad + extras. "
           "Generated from the data, so it stays in sync with the recipes and "
           "the grocery list.", ""]

    out.append("| Day | Protein anchor | Cooked veg | Salad | Extras |")
    out.append("| --- | --- | --- | --- | --- |")
    for d in plan.get("days", []):
        extras = ", ".join(name(x) for x in d.get("extras", []))
        out.append(f"| {d['day']} | {name(d.get('protein',''))} | "
                   f"{name(d.get('cooked_veg',''))} | {name(d.get('salad',''))} | {extras} |")
    out.append("")

    out.append("## Cook once, eat through the week\n")
    out.append("The plan above works because most of it is batch-prepped. "
               "Number of batches to cook this week:\n")
    out.append("| Recipe | Batches | Keeps |")
    out.append("| --- | --- | --- |")
    for rid, n in sorted(plan.get("batches", {}).items(), key=lambda kv: name(kv[0])):
        st = _storage_line(recipes.get(rid, {}).get("storage")) if rid in recipes else ""
        out.append(f"| {name(rid)} | {n} | {st} |")
    out.append("")
    return "\n".join(out)
