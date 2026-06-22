"""Render data-layer content into Markdown pages.

Every function returns a Markdown string. The mkdocs build (docs/gen_pages.py)
and the local preview script both call these, so the website and any other
surface render from identical logic.
"""
from . import data
from . import webdata
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


def render_grocery_page():
    mp = data.meal_plan()
    batches = mp.get("batches", {})

    out = ["# Grocery List", "",
           "This list follows your [meal plan](meal-plan.md). Choose what to "
           "shop for — your whole plan, a single day, or just one meal — and "
           "tick things off as you go. Condiments and batch items (dips, nuts, "
           "chaas) count as one make-ahead batch, not once per day.", "",
           # JS builds the selector + list here from your saved plan.
           '<div id="pp-grocery-app" markdown="0"></div>', ""]

    # No-JS fallback: the default week, aggregated in Python.
    out.append('<div id="pp-grocery-fallback" markdown="1">')
    out.append("")
    out.append("_Showing the default week. Enable JavaScript to shop for a "
               "single day or meal from your own plan._")
    out.append("")
    out.append(_grocery_list_md(batches))
    out.append("</div>")
    out.append("")

    # Data for the browser (recipes pre-resolved to grocery contributions).
    out.append('<script type="application/json" id="pp-data">'
               + webdata.to_json() + "</script>")
    return "\n".join(out)


# --------------------------------------------------------------------------
# 7-day meal plan page
# --------------------------------------------------------------------------
def render_meal_plan_page():
    recipes = data.recipes()
    plan = data.meal_plan()
    pay = webdata.payload()
    options = pay["options"]

    def name(rid):
        return recipes[rid]["name"] if rid in recipes else rid

    def esc(s):
        return (str(s).replace("&", "&amp;").replace("<", "&lt;")
                .replace(">", "&gt;"))

    def select(slot, day, current):
        opts = []
        for rid, label in options[slot]:
            sel = " selected" if rid == current else ""
            opts.append(f'<option value="{rid}"{sel}>{esc(label)}</option>')
        return (f'<select class="pp-pick" data-day="{esc(day)}" '
                f'data-slot="{slot}" data-default="{current}">'
                + "".join(opts) + "</select>")

    out = ["# Build Your Meal Plan", "",
           f"A starting plan for a family of {plan.get('servings', 4)} — "
           "**swap any meal from the dropdowns** to make it yours. Your choices "
           "are saved on this device, and the [grocery list](grocery-list.md) "
           "follows whatever plan you build.", "",
           '<div class="pp-duration" role="group" aria-label="Plan length">',
           '  <span class="pp-duration__label">Show</span>',
           '  <button type="button" data-days="1">1 day</button>',
           '  <button type="button" data-days="3">3 days</button>',
           '  <button type="button" data-days="7" aria-pressed="true">7 days</button>',
           '  <button type="button" class="pp-plan-reset">Reset to default</button>',
           '</div>', ""]

    # Editable plan as one card per day: stacked, full-width fields that read
    # well on a phone and flow into 2-3 columns on wider screens. Raw HTML so
    # the cards can hold <select> and carry the data-day-index the filter uses.
    out.append('<div class="pp-planner" markdown="0">')
    for i, d in enumerate(plan.get("days", [])):
        day = d["day"]
        extras = ", ".join(name(x) for x in d.get("extras", []))
        out.append(f'<div class="pp-day" data-day="{esc(day)}" data-day-index="{i}">')
        out.append(f'<h3 class="pp-day__name">{esc(day)}</h3>')
        out.append('<div class="pp-field"><label>Protein anchor</label>'
                   + select("protein", day, d.get("protein", "")) + "</div>")
        out.append('<div class="pp-field"><label>Cooked veg</label>'
                   + select("cooked_veg", day, d.get("cooked_veg", "")) + "</div>")
        out.append('<div class="pp-field"><label>Salad</label>'
                   + select("salad", day, d.get("salad", "")) + "</div>")
        if extras:
            out.append('<p class="pp-day__extras"><span>Extras</span>'
                       + esc(extras) + "</p>")
        out.append("</div>")
    out.append("</div>")
    out.append("")
    out.append("_Extras (drinks, dips, nuts) stay as the default accompaniments "
               "and are included in the grocery list._")
    out.append("")

    out.append("## Cook once, eat through the week\n")
    out.append("Most of the default plan is batch-prepped. Batches to cook for "
               "the starting week:\n")
    out.append("| Recipe | Batches | Keeps |")
    out.append("| --- | --- | --- |")
    for rid, n in sorted(plan.get("batches", {}).items(), key=lambda kv: name(kv[0])):
        st = _storage_line(recipes.get(rid, {}).get("storage")) if rid in recipes else ""
        out.append(f"| {name(rid)} | {n} | {st} |")
    out.append("")
    return "\n".join(out)
