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
registered via `extra_css` / `extra_javascript` in `mkdocs.yml`. The chosen count
is remembered across reloads — see Phase 2.3.

## 2.3 Persistent state (localStorage)

**What changed.** Two reader settings now survive a page refresh, which matters
in the one place it's used most — standing in a shop:

- **Grocery checkboxes** are clickable and persistent. Tick items off; a reload
  (or coming back later) keeps your progress. A small toolbar shows
  *"N / M in the basket"* with a **Reset** button, and checked items are muted
  and struck through.
- **The serving count** (1 / 2 / 4 / 6) is remembered, so the Recipes page opens
  at the size you last cooked for.

**How it's wired.** `pymdownx.tasklist` is set to `clickable_checkbox: true` so
the rendered checkboxes aren't disabled. `docs/assets/js/grocery-checklist.js`
stores each box under `pp-check:<page>|<ingredient-name>` — keyed by the name
*before* the quantity, so ticks stay valid even when amounts change. The serving
scaler stores its choice under `pp-servings` and re-applies it on load. All
storage is wrapped in try/catch so a privacy-locked browser degrades gracefully
rather than breaking the page. State is per-device (localStorage), which is the
right scope for a personal shopping list.

## 2.5 Flexible meal-plan & grocery scope

**What changed.** Not everyone cooks a full week at once, so the plan and the
shopping list are now scopeable:

- The **Meal Plan** page has a *Show 1 / 3 / 7 days* control that trims the plan
  table to the length you actually want.
- The **Grocery List** page has a *Shopping for* picker: the whole week, any
  single day, any 3-day stretch, or **a single meal of your choice** — so you can
  shop for exactly one dinner if that's all you need. The chosen list's
  checkboxes and basket count work just as before.

**How it's wired.** Every scope's list is still aggregated in **Python**
(`grocery.aggregate` already accepts any `{recipe: count}` map), so the amounts
can never disagree with the recipes — there's no shopping-list maths duplicated
in JavaScript. `render.py` pre-renders one list per scope inside an
`md_in_html` `<div data-scope=…>` (using bold category labels, not headings, to
keep 30-plus lists out of the page's table of contents). `grocery-scope.js` only
shows the selected list and rebinds the checkbox persistence + toolbar to it (it
replaces the old `grocery-checklist.js`). The meal-plan control is a small
row-filter (`meal-plan.js`). The Keto chapter also gained a sourced
*"how often should you eat?"* section (keto is defined by macros, not meal
timing; 2–3 meals a day is the recommended norm).

## 2.4 Installable, offline PWA

**What changed.** ProteinPlate is now a Progressive Web App. On a phone you can
"Add to Home Screen" and it launches full-screen like a native app, with its own
plate-and-cutlery icon. Once visited, it works **offline** — the grocery list,
recipes and plan are all available in the aisle with no signal, and the
persistent checkboxes (Phase 2.3) keep working.

**How it's wired.**

- **`docs/manifest.json`** declares the app (name, standalone display, green theme,
  icons). Paths are relative so it works at `/` or under a project subpath. (We use
  `.json`, not `.webmanifest`, because GitHub Pages can serve the latter with the
  wrong MIME type.)
- **`docs/sw.js`** is the service worker, deliberately placed at the **site root**
  so its scope covers the whole app (a worker can't control paths above itself).
  It precaches the app shell on install, serves navigations network-first (fresh
  when online, cached when not, home as last resort), and cache-fills other GETs.
  A `VERSION` constant rolls the cache when the shell changes.
- **`overrides/main.html`** (via `theme.custom_dir`) injects the
  `<link rel="manifest">`, `theme-color`, and Apple touch-icon tags into every
  page's head, using Material's `base_url` so the subpath is handled.
- **`docs/assets/js/pwa.js`** registers the worker, deriving the site base from
  the manifest link's URL — no hardcoded repo name.
- **Icons** (`docs/assets/icons/`) are 192/512 plus a maskable variant, generated
  to match the theme.

Service workers require a secure context, which both `mkdocs serve` (localhost)
and GitHub Pages (HTTPS) provide. Verify in the browser via DevTools →
Application → Manifest / Service Workers, and the install prompt.

---

# Phase 3 — Backlog plan (sequenced)

The remaining work, ordered by **dependencies, importance, usefulness, and how
approachable each piece is**. Principle: cheap protective guardrails first, then
the single highest-value feature, then refinements, then the big deferred lift.

| # | Item | Effort | Depends on | Importance | Why here |
|---|------|--------|-----------|-----------|----------|
| 3.1 | Guardrails & safety note | Low | — | High | No dependencies, protects the Phase 1.4 fix, and a health caution is overdue. Quick, understandable wins first. |
| 3.2 | Verified macros | Med–High | schema slots (done) | High | The biggest trust lever and core to the project's promise. |
| 3.3 | Dry→weight grocery conversion | Med | `units.py`, registry | Medium | Natural extension of unit normalization; finishes the grocery story — do alongside 3.2 while enriching the registry. |
| 3.4 | Recipe JSON-LD | Low–Med | macros (3.2) | Medium | Richer search results once nutrition exists; fits the generate-from-data pattern. |
| 3.5 | i18n + units toggle | High | stable everything | Low now / High later | Largest lift; English-only is the current scope, so it's intentionally last. |

## 3.1 Guardrails & safety
- **No-stub CI guard** — a check that fails the build if any page is a near-empty
  placeholder, so a page can never silently regress (as in Phase 1.4). A small
  script wired into the existing validate workflow.
- **Health-scope note** — a short "who this isn't for" caution (pregnancy, kidney
  disease, type-1 diabetes, eating-disorder history) on About / Keto. Low effort,
  high responsibility for a health-adjacent guide.
- *Done when:* CI rejects a stub page; the caution is live.

## 3.2 Verified macros
- Source per-ingredient per-100 g values (kcal, protein, carbs, fat) from a cited
  database — USDA FoodData Central, or IFCT 2017 for Indian foods — into the
  registry's macro slots; compute per serving; render on each recipe; mark
  `verified: true` only after a human check. The validator flags missing/unverified.
- *Why the care:* wrong nutrition on a health site is worse than none — human in
  the loop, sources cited. (The schema was built for this in Phase 1.)
- *Done when:* every recipe shows sourced, verified per-serving macros.

## 3.3 Dry→weight grocery conversion
- Add a per-ingredient yield/density to the registry so cooked-volume amounts
  ("4½ cup boiled chickpeas") convert to a purchasable weight of the dry good
  ("~250 g dry chana"). Extends `units.py` and the `purchase_as` mapping — the one
  refinement left from Phase 2.1.
- *Done when:* `purchase_as` items show a buyable weight, not a cooked volume.

## 3.4 Recipe JSON-LD
- Emit `schema.org/Recipe` structured data per recipe from the data (ingredients,
  steps, image, and nutrition from 3.2), so search engines show rich results —
  serving the "accessible worldwide" goal through discovery.
- *Done when:* each recipe page carries valid Recipe JSON-LD.

## 3.5 Internationalisation (deferred)
- Translation infrastructure (`mkdocs-static-i18n`), parallel content overlays,
  and a metric/imperial units toggle for non-metric shoppers. Largest change;
  English-only is the current scope, so this is intentionally last.
- *Cheap prep meanwhile:* keep user-facing strings clean and avoid baking numbers
  into prose, so translation stays inexpensive when the time comes.

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
