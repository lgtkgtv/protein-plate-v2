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


def _qty_span(qty, base_servings, scales):
    """Wrap a numeric quantity so the client-side serving scaler can rescale it."""
    return (f'<span class="pp-qty" data-qty="{qty:g}" '
            f'data-base="{base_servings}" data-scale="{1 if scales else 0}">'
            f'{_num(qty)}</span>')


def _ingredient(ig, base_servings=None, scalable=False):
    item = ig["item"]
    name = data.display_name(item)
    prep = f" ({ig['prep']})" if ig.get("prep") else ""
    opt = " *(optional)*" if ig.get("optional") else ""
    qty, unit = ig.get("qty"), ig.get("unit")
    if qty is None or unit in ("to_taste", "as_needed", "to_cover"):
        word = {"to_taste": "to taste", "as_needed": "as needed",
                "to_cover": "to cover"}.get(unit, "as needed")
        return f"{name} {word}{prep}{opt}"
    # numeric quantity
    if scalable:
        num = _qty_span(qty, base_servings, ig.get("scale", True))
    else:
        num = _num(qty)
    if unit == "piece":
        return f"{num} {name}{prep}{opt}"
    return f"{num} {unit} {name}{prep}{opt}"


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
           "nuts/seeds.", "",
           '<div class="pp-servings" role="group" aria-label="Adjust servings">',
           '  <span class="pp-servings__label">Show recipes for</span>',
           '  <button type="button" data-servings="1">1</button>',
           '  <button type="button" data-servings="2">2</button>',
           '  <button type="button" data-servings="4" aria-pressed="true">4</button>',
           '  <button type="button" data-servings="6">6</button>',
           '  <span class="pp-servings__suffix">people</span>',
           '</div>',
           "",
           "_Spices, oil and salt stay fixed when you rescale; batch items "
           "(dips, toasted nuts) are made in bulk and don't rescale._", ""]
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
            scalable = r["category"] != "condiment"
            bs = r["base_servings"]
            ings = " · ".join(
                _ingredient(i, base_servings=bs, scalable=scalable)
                for i in r["ingredients"])
            if scalable:
                label = (f'**Ingredients** (for '
                         f'<span class="pp-srv" data-base="{bs}">{bs}</span>): ')
            else:
                noun = "makes ~" if r.get("batch") else "serves "
                label = f"**Ingredients** ({noun}{bs}): "
            out.append(f"{label}{ings}\n")
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
def _grocery_list_md(counts):
    """Render one categorised checklist for a given {recipe_id: count} map.

    Category titles are bold paragraphs, not headings, so the many pre-rendered
    scope lists don't flood the page's table of contents with duplicate anchors.
    """
    totals, to_taste, notes = aggregate(counts)
    lines = []
    for cat, heading in CATEGORY_ORDER:
        rows = [t for t in totals if t["category"] == cat]
        extras = [d for d in to_taste.get(cat, [])
                  if not any(t["display"] == d for t in rows)]
        if not rows and not extras:
            continue
        lines.append(f"**{heading}**\n")
        for t in rows:
            amount = " + ".join(f"{_num(q)} {u}" for q, u in t["amounts"])
            note = f"  *({notes[t['display']]})*" if t["display"] in notes else ""
            lines.append(f"- [ ] {t['display']} — {amount}{note}")
        for d in extras:
            note = f"  *({notes[d]})*" if d in notes else ""
            lines.append(f"- [ ] {d} — to taste / as needed{note}")
        lines.append("")
    return "\n".join(lines)


def _day_counts(day):
    counts = {}
    for slot in ("protein", "cooked_veg", "salad"):
        if day.get(slot):
            counts[day[slot]] = counts.get(day[slot], 0) + 1
    for rid in day.get("extras", []):
        counts[rid] = counts.get(rid, 0) + 1
    return counts


def render_grocery_page():
    mp = data.meal_plan()
    recipes = data.recipes()
    days = mp.get("days", [])
    batches = mp.get("batches", {})

    # Build every shopping scope: (value, label, {recipe: count}).
    scopes = [("week", "Whole week (7 days)", batches)]
    for d in days:
        scopes.append((f"day:{d['day']}", d["day"], _day_counts(d)))
    for i in range(len(days) - 2):                      # 3 consecutive days
        window = days[i:i + 3]
        counts = {}
        for d in window:
            for rid, n in _day_counts(d).items():
                counts[rid] = counts.get(rid, 0) + n
        scopes.append((f"d3:{window[0]['day']}",
                       f"{window[0]['day']}\u2013{window[2]['day']}", counts))
    for rid in sorted(recipes, key=lambda r: recipes[r]["name"]):
        scopes.append((f"meal:{rid}", recipes[rid]["name"], {rid: 1}))

    out = ["# Grocery List", "",
           "Pick what you're shopping for — the whole week, a single day, a "
           "3-day stretch, or just one meal — then tick items off as you go. "
           "Each list is generated from the recipe data, so the amounts always "
           "match the plates.", ""]

    # Scope selector (progressively enhanced; the week list shows without JS).
    out.append('<div class="pp-scope" markdown="0">')
    out.append('  <label for="pp-scope-select">Shopping for</label>')
    out.append('  <select id="pp-scope-select" class="pp-scope__select">')
    groups = [("day:", "A single day"), ("d3:", "3 days from"),
              ("meal:", "A single meal")]
    out.append('    <option value="week" selected>Whole week (7 days)</option>')
    for prefix, glabel in groups:
        out.append(f'    <optgroup label="{glabel}">')
        for v, lbl, _c in scopes:
            if v.startswith(prefix):
                out.append(f'      <option value="{v}">{lbl}</option>')
        out.append('    </optgroup>')
    out.append('  </select>')
    out.append('</div>')
    out.append("")

    # One pre-rendered list per scope; all hidden except the week.
    for v, lbl, counts in scopes:
        hidden = "" if v == "week" else " hidden"
        out.append(f'<div class="pp-scope-list" data-scope="{v}" markdown="1"{hidden}>')
        out.append("")
        out.append(_grocery_list_md(counts))
        out.append('</div>')
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
           "the grocery list.", "",
           '<div class="pp-duration" role="group" aria-label="Plan length">',
           '  <span class="pp-duration__label">Show</span>',
           '  <button type="button" data-days="1">1 day</button>',
           '  <button type="button" data-days="3">3 days</button>',
           '  <button type="button" data-days="7" aria-pressed="true">7 days</button>',
           '</div>',
           "",
           "_Need to shop for just part of the week? The "
           "[grocery list](grocery-list.md) can be scoped to a single day or "
           "even a single meal._", ""]

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
