# Design & Architecture

This document is the story of how ProteinPlate v2 is built — the planning, the
design decisions, and how the pieces are wired together. It's organised by
**phase** so it's easy to follow the project's evolution rather than reading it
all at once.

Companion docs: [`SCHEMA.md`](SCHEMA.md) (the recipe data contract) and
[`WIRING.md`](WIRING.md) (how the site is generated from the data).

---

## The core idea

v1 was a hand-written [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)
site — every page authored as Markdown by hand. It worked, but the same facts
(a recipe's ingredients, the grocery list, the meal plan) lived in three places
that could drift apart.

**v2 makes the recipe data the single source of truth.** Pages that are really
*views* of that data — Recipes, Ingredients, Grocery List, Meal Plan — are
**generated at build time**. Narrative pages (Home, The Plate, Keto, About) stay
hand-written. Editing one YAML file updates every view at once.

## Architecture at a glance

```
data/*.yaml ──▶ proteinplate (data · grocery · units · render) ──┬──▶ website pages (mkdocs)
                                                                  └──▶ CLI / tests / future app
```

| Layer | Lives in | Responsibility |
| ----- | -------- | -------------- |
| Data | `data/` | Recipes, ingredient registry, meal plan — the source of truth |
| Contract | `schema/recipe.schema.json` | Machine-enforced shape of a recipe |
| Core | `proteinplate/` | Load data, aggregate, normalize units, render Markdown |
| Build hook | `docs/gen_pages.py` | Generates the 4 data-driven pages during `mkdocs build` |
| Narrative | `docs/*.md` | Hand-written pages + images |
| CLI / tests | `scripts/`, `tests/` | Same core, used outside the website |

---

# Phase 1 — The data-driven rebuild

Goal: keep v1's content, but drive the data-shaped pages from one source.

## 1.1 Recipe data schema

All 20 recipes became one YAML file each under `data/recipes/`, plus a canonical
ingredient registry. Key decisions:

- **YAML for authoring** — contributors edit plain text, matching the
  "markdown-first" philosophy. No HTML, no build step to add a recipe.
- **A registry, not repeated metadata** — `ingredients.yaml` holds each
  ingredient's grocery aisle, aliases, and "buy X to make Y" mapping *once*.
  Recipes reference ingredients by id. Without this, "onion" would carry its
  aisle in 11 files and drift out of sync.
- **`scale: false` on spices, oil and salt** — so the serving scaler (Phase 2.2)
  never doubles the chilli when you cook for more people.
- **Macros left null / `verified: false`** — we do not invent nutrition numbers.
  The schema holds them; a future sourced + human-checked pass fills them in.
- **A JSON Schema contract + validator** — `scripts/validate.py` checks every
  recipe against `schema/recipe.schema.json` *and* the cross-references (every
  ingredient resolves, every plan entry exists). It runs in CI on every change.

Full field reference: [`SCHEMA.md`](SCHEMA.md).

## 1.2 Wiring the website to the data

The four data-shaped pages are generated, not committed:

- **`mkdocs-gen-files`** runs `docs/gen_pages.py` during the build, which imports
  `proteinplate` and writes `recipes.md`, `ingredients.md`, `grocery-list.md`,
  and `meal-plan.md` into the virtual docs tree. They never exist as source
  files, so they can't drift from the data.
- **`proteinplate/` is an importable core** shared by the website, the CLI, and
  the tests — one copy of the render/aggregate logic, so surfaces stay identical.
- **`data/meal_plan.yaml` drives two pages**: the Meal Plan page (the `days`) and
  the Grocery List (the `batches`).

Mechanics and how to apply it: [`WIRING.md`](WIRING.md).

## 1.3 Repository & tooling

- **New repo `protein-plate-v2`** — v2 is a structural rewrite, so it stands on
  its own rather than forcing onto v1's history. Code is MIT, content is
  CC BY 4.0 with attribution back to v1.
- **`uv` for the environment** — `pyproject.toml` is the single source of truth
  for dependencies, pinned by `uv.lock`. `requirements.txt` was removed to avoid
  two dependency lists. `[tool.uv] package = false` keeps this an app, not a
  library. CI uses `astral-sh/setup-uv` + `uv sync --locked`.
- **MkDocs ecosystem pin** — after the 2026 MkDocs schism, `mkdocs-gen-files`
  0.6+ began pulling in `properdocs`, which injects a promotional warning. We pin
  `mkdocs-gen-files<0.6` to drop that dependency, and set `NO_MKDOCS_2_WARNING`
  for Material's own banner. See the note at the end of [`WIRING.md`](WIRING.md).

## 1.4 Content parity restoration

The first wiring pass left the four narrative pages as one-line **stubs** and
never copied v1's images or full theme config — so the deployed site was a
skeleton. Fixed by:

- Porting v1's Home, The Plate, Keto, and About pages and **all 9 food photos**
  into `docs/`.
- Restoring full theme parity in `mkdocs.yml`: green/deep-orange palette, logo,
  the complete feature and extension set (`pymdownx.details`, `md_in_html`,
  `toc.permalink`), copyright, and social link — while keeping the v2 plugins.
- Making the generated Recipes page render each recipe's photo (`media.image`).

**Lesson recorded:** generated pages come from data; narrative pages are real,
version-controlled Markdown. A future "no-stub" CI guard (see roadmap) will stop
a page silently regressing to a placeholder again.

---

# Phase 2 — Beyond v1

Goal: make v2 genuinely better and more maintainable than v1.

## 2.1 Unit normalization (grocery list)

**What changed.** A new `proteinplate/units.py` groups each ingredient's
quantities by physical dimension and sums the convertible ones, so the grocery
list shows one tidy amount per item:

| Before | After |
| ------ | ----- |
| Oil — `1 tbsp` + `2 tsp` + … (multiple lines) | Oil — **¾ cup** |
| Besan — `2 cup` + `2 tbsp` + `2 tsp` | Besan — **4¼ cup** |
| Curd — `cup` + `tbsp` | Curd — **6½ cup** |
| Chicken — `g` lines | Chicken — **1.6 kg** |

The logic is deliberately conservative: volume rolls up through tsp → tbsp → cup
(litres only past 2 L), mass through g → kg, and **count/fuzzy units stay
separate** — so coriander reads *2¼ cup + 2 handful* and lemon *5 tbsp + 4½
piece*. Those two-part lines are honest: you can't convert a handful or a whole
lemon into spoons without yield data, which is left as the one remaining
refinement (dry→cooked/weight conversion for `purchase_as` items).

**How it's wired.** `grocery.aggregate()` collects every `(qty, unit)` per
ingredient and calls `units.normalize()`; the website grocery page and the CLI
both go through it, so they stay identical. `tests/test_grocery_units.py` covers
the conversions (6/6 passing, runnable with
`uv run python tests/test_grocery_units.py`, no pytest dependency).

## 2.2 Serving scaler (1 / 2 / 4 / 6 people)

**What changed.** The Recipes page now has a *Show recipes for 1 · 2 · 4 · 6
people* control that rescales every recipe's quantities live in the browser. A
single person is supported, not just families.

The scaling respects the data: quantities marked `scale: false` (spices, oil,
salt) and "to taste" items **stay fixed** — picking 6 people doesn't sextuple the
turmeric. Batch items and condiments (dips, toasted nuts) don't rescale either;
they're made in bulk, and their label reads *makes ~N* / *serves N* instead.

**How it's wired.** `render.py` wraps each numeric quantity in a
`<span class="pp-qty" data-qty data-base data-scale>` carrying the base amount,
the recipe's base servings, and whether it scales. `docs/assets/js/serving-scaler.js`
reads the selected count and recomputes each span (`base × target / base_servings`
for scalable items, unchanged otherwise), reformatting fractions. Styling is in
`docs/assets/css/extra.css`, themed with Material's CSS variables, and both are
registered via `extra_css` / `extra_javascript` in `mkdocs.yml`. Selection is
in-memory for now; persistence arrives with Phase 2.3.

---

# Roadmap / backlog

In rough priority:

1. **Persistent checkboxes** (Phase 2.3) — the grocery list already renders real
   checkboxes; add `localStorage` so ticks (and the chosen serving count) survive
   a refresh.
2. **PWA** (Phase 2.4) — installable, offline grocery checklist for the store.
3. **Verified macros** — fill the schema's macro slots from USDA FDC / IFCT with a
   human check.
4. **Dry→weight grocery conversion** — turn "4½ cup boiled chickpeas" into grams
   of dry chana using per-ingredient yields.
5. **No-stub CI guard** — fail the build if any page is a placeholder, so the
   Phase 1.4 regression can't recur.
6. **schema.org `Recipe` JSON-LD + i18n** — richer search results and translation
   readiness.

---

# Conventions for contributors

- **Content lives in `data/`** — never edit the generated pages (`recipes.md`,
  `ingredients.md`, `grocery-list.md`, `meal-plan.md`); they don't exist as
  source. Narrative pages (`docs/index.md`, `the-plate.md`, `keto.md`, `about.md`)
  are hand-written.
- **Add a recipe**: copy a `data/recipes/*.yaml`, edit it, add any new ingredient
  to `data/ingredients.yaml`, then `uv run python scripts/validate.py`.
- **The core is shared**: website, CLI, and tests all import `proteinplate`, so a
  change there updates every surface at once.

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the step-by-step.
