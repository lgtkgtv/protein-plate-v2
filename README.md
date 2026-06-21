# 🍽️ ProteinPlate v2

[![Validate recipe data](https://github.com/lgtkgtv/protein-plate-v2/actions/workflows/validate-data.yml/badge.svg)](https://github.com/lgtkgtv/protein-plate-v2/actions/workflows/validate-data.yml)
[![Code: MIT](https://img.shields.io/badge/Code-MIT-yellow.svg)](LICENSE)
[![Content: CC BY 4.0](https://img.shields.io/badge/Content-CC%20BY%204.0-lightgrey.svg)](LICENSE-CONTENT)

> A free, open guide to **high-protein, lower-calorie Indian home meals** —
> annotated plates, family-of-4 recipes, batch-cooking plans, grocery lists, and
> a keto chapter. Built for public good.

**v2 is a structural rewrite of [ProteinPlate v1](https://github.com/lgtkgtv/protein-plate).**
The content is the same practical guide; what changed is the engineering: every
recipe is now **structured data**, and the website pages are **generated from it**
so they can never drift out of sync.

[Live site](https://lgtkgtv.github.io/protein-plate-v2/) · [Report an issue](https://github.com/lgtkgtv/protein-plate-v2/issues)

---

## What's different in v2

| | v1 | v2 |
|---|----|----|
| Recipes | hand-written Markdown | one structured YAML file each (`data/recipes/`) |
| Grocery list / meal plan | hand-maintained tables | **generated** from the data at build time |
| Source of truth | the prose on each page | the data layer — site, CLI and any future app render from it |
| Safety net | none | JSON Schema + CI validation on every change |

```
data/*.yaml ──▶ proteinplate (data · grocery · render) ──┬──▶ website pages (mkdocs)
                                                          └──▶ CLI / future PWA / API
```

## Repository layout

```
data/                  single source of truth
  ingredients.yaml     canonical ingredient registry (aisle, aliases, macros slot)
  recipes/*.yaml       20 recipes, one file each
  meal_plan.yaml       drives BOTH the meal-plan page and the grocery list
proteinplate/          importable core, shared by every surface
  data.py grocery.py render.py
docs/
  gen_pages.py         mkdocs-gen-files hook -> generates 4 pages at build time
  index.md the-plate.md keto.md about.md   (hand-written narrative)
schema/recipe.schema.json   the enforced contract
scripts/               validate.py · build_grocery_list.py · preview_pages.py
mkdocs.yml  pyproject.toml  uv.lock  .python-version
SCHEMA.md   WIRING.md  (design + architecture docs)
```

## Quick start

This project uses [uv](https://docs.astral.sh/uv/) to manage the Python
environment. [Install uv](https://docs.astral.sh/uv/getting-started/installation/)
once, then:

```bash
git clone https://github.com/lgtkgtv/protein-plate-v2.git
cd protein-plate-v2
uv sync                               # creates .venv from pyproject.toml + uv.lock

uv run python scripts/validate.py     # gate: schema + cross-references
NO_MKDOCS_2_WARNING=true uv run mkdocs serve   # live preview (the env var hides Material's MkDocs-2.0 banner)
```

Edit any file in `data/`, save, and the affected pages regenerate instantly.

## Add or change a recipe

1. Copy an existing `data/recipes/*.yaml` and edit it.
2. If you use a new ingredient, add it to `data/ingredients.yaml`.
3. Run `uv run python scripts/validate.py`. Green means the Recipes, Ingredients and
   Grocery pages will all update consistently — see [`SCHEMA.md`](SCHEMA.md).

## How deployment works

Pushing to `main` runs `.github/workflows/deploy.yml`, which installs deps,
builds the site (generating the data-driven pages), and publishes to the
`gh-pages` branch. GitHub Pages serves it at `lgtkgtv.github.io/protein-plate-v2/`.

## License

- **Code & configuration:** [MIT](LICENSE)
- **Written content, recipes & guide:** [CC BY 4.0](LICENSE-CONTENT), building on
  ProteinPlate v1.

## ⚠️ Disclaimer

ProteinPlate is **general food and wellness information, not medical or dietetic
advice.** Calorie and protein needs are personal. Consult a registered dietitian
or doctor before a calorie-restricted or ketogenic diet, especially with any
medical condition. Nutrition numbers, where present, are estimates pending a
source-verified pass.
