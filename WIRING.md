# Wiring the website to the data

The four content pages that used to be hand-maintained Markdown —
**Recipes, Ingredients & Portions, Meal Plan, Grocery List** — are now
**generated at build time** from the YAML data layer. They are never committed,
so the site cannot drift from the data. Narrative pages (Home, The Plate, Keto,
About) stay as ordinary Markdown.

## How it fits together

```
data/                      one source of truth
  ingredients.yaml
  recipes/*.yaml
  meal_plan.yaml           drives BOTH the meal-plan page and the grocery list
proteinplate/              importable core (shared by site, CLI, future app/API)
  data.py    grocery.py    render.py
docs/
  gen_pages.py             mkdocs-gen-files hook -> writes the 4 pages at build time
  index.md the-plate.md keto.md about.md   (hand-written, unchanged)
mkdocs.yml                 adds the gen-files plugin + the generated pages in nav
```

At build time `mkdocs` runs `docs/gen_pages.py`, which imports `proteinplate`
and writes `recipes.md`, `ingredients.md`, `grocery-list.md`, `meal-plan.md`
into the virtual docs tree. The same `render.*` functions back the CLI, so the
terminal grocery list and the website grocery page are byte-identical.

```
                    ┌── proteinplate.render ──┐
data/*.yaml ──▶ ────┤                          ├──▶ website pages (mkdocs)
                    └── proteinplate.grocery ──┴──▶ CLI / future app / API
```

## In this repo (v2 is greenfield)

Nothing to migrate — v2 ships wired. The four data-driven pages
(`recipes`, `ingredients`, `grocery-list`, `meal-plan`) have **no source file** in
`docs/`; they are produced by `docs/gen_pages.py` during the build and listed in
the `nav`. Only the narrative pages (`index`, `the-plate`, `keto`, `about`) exist
as Markdown. Add a recipe by editing `data/` — see `CONTRIBUTING.md`.

## Dependencies (pyproject.toml)

Dependencies live in `pyproject.toml` and are pinned in `uv.lock`:

```toml
[project]
dependencies = [
    "mkdocs-material>=9.5",
    "mkdocs-gen-files>=0.5",
    "pyyaml>=6.0.1",
    "jsonschema>=4.18",
]
```

`pyyaml` is what `proteinplate` uses to read the data at build time;
`jsonschema` is for `scripts/validate.py` in CI. `uv sync` installs exactly
what `uv.lock` records. (Need a `requirements.txt` for some other tool? Generate
one on demand with `uv export --no-hashes -o requirements.txt`.)

## Local workflow

```bash
uv sync
uv run python scripts/validate.py            # gate: schema + cross-refs + plan refs
uv run mkdocs serve                           # live preview, pages regenerate on edit
uv run python scripts/build_grocery_list.py  # same grocery list, in the terminal
uv run python scripts/preview_pages.py       # dump generated .md to data/_generated_preview/
```

## What changes for contributors

Editing a recipe is still "edit one plain-text file." But now editing
`data/recipes/paneer-bhurji.yaml` updates the Recipes page, the Ingredients page,
and (if it's in the plan) the Grocery List — automatically, with no chance of the
three disagreeing. CI (`.github/workflows/validate-data.yml`) blocks any change
that breaks the schema or references an unknown ingredient/recipe.

## Deploy

The GitHub Pages deploy workflow installs the environment with `uv sync --locked`
and the `proteinplate/` package is present in the repo. Pushing to `main` builds
(now generating the four pages) and publishes.

## A note on the MkDocs ecosystem (2026)

In early 2026 the MkDocs project fractured: an announced **MkDocs 2.0** rewrite
would drop the plugin system (breaking Material and every plugin), the **Material**
team began steering users to its own successor **Zensical**, and a former
maintainer launched **ProperDocs**, a MkDocs 1.x fork, after a contested PyPI
takeover. As a result, builds now print warning banners.

This project deliberately stays on **plain MkDocs 1.x + Material** for now and
takes one defensive measure:

- **`mkdocs-gen-files` is pinned `<0.6`.** Version 0.6+ added a hard dependency on
  `properdocs`, which injects a "switch to ProperDocs" ad into every build. 0.5.x
  has the same API and depends only on `mkdocs`, so the ad disappears entirely.
- **Material's own MkDocs-2.0 banner** is suppressed automatically in `--strict`
  (used by the deploy workflow). For local `uv run mkdocs serve`, silence it with
  `NO_MKDOCS_2_WARNING=true`.

`uv.lock` pins every transitive version, so a surprise upstream change can't alter
your build until you choose to `uv lock` again. Revisit the choice before
Material's support window ends (~November 2026); Zensical is the path to watch.
