# Contributing to ProteinPlate v2

Thanks for helping. The golden rule of v2: **content lives in `data/`, never in
the generated pages.** Editing the data updates every page consistently; editing
a generated page would be overwritten on the next build.

## Add a recipe

1. Copy an existing file in `data/recipes/` to `data/recipes/<your-id>.yaml`
   (the `id` field must equal the filename without `.yaml`).
2. Fill in the fields — see [`SCHEMA.md`](SCHEMA.md) for the full reference.
3. Every ingredient `item` must exist in `data/ingredients.yaml`. Add new ones
   there with a `grocery_category`.
4. Validate:
   ```bash
   uv sync
   uv run python scripts/validate.py
   ```
5. Preview: `uv run mkdocs serve`, or `uv run python scripts/preview_pages.py` to dump the
   generated Markdown without running the site.

CI runs `validate.py` on every push and pull request; a red check blocks merge.

## What's welcome

- New recipes and corrections to portions or steps
- Verified macros (cite the source — USDA FoodData Central or IFCT — and set
  `verified: true` only after a human check)
- Translations (see the i18n note in `SCHEMA.md`)
- Bug fixes in `proteinplate/` or `scripts/`

## What to avoid

- Don't edit `recipes.md`, `ingredients.md`, `grocery-list.md` or `meal-plan.md`
  directly — they don't exist as source files; they're generated.
- Don't invent nutrition numbers. A null macro is better than a wrong one.

## Style

Keep recipes short and practical. Real quantities in grams where it matters.
One protein anchor per recipe; sides, salads and condiments stay in their
categories.
