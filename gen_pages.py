"""mkdocs-gen-files hook.

Runs during `mkdocs build` / `mkdocs serve` and writes the data-driven pages
straight into the virtual docs tree — they are NOT committed to the repo, so the
site can never drift from the data. Narrative pages (Home, The Plate, Keto,
About) stay as normal hand-written Markdown in docs/.
"""
import os
import sys

# Make the `proteinplate` package importable regardless of mkdocs' cwd.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import mkdocs_gen_files  # noqa: E402
from proteinplate import render  # noqa: E402

PAGES = {
    "recipes.md": render.render_recipes_page,
    "ingredients.md": render.render_ingredients_page,
    "grocery-list.md": render.render_grocery_page,
    "meal-plan.md": render.render_meal_plan_page,
}

for path, fn in PAGES.items():
    with mkdocs_gen_files.open(path, "w") as f:
        f.write(fn())
