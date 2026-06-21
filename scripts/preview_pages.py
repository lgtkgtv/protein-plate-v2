#!/usr/bin/env python3
"""Render the data-driven pages to plain .md (no mkdocs needed) for inspection/CI."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from proteinplate import render

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "_generated_preview")
os.makedirs(OUT, exist_ok=True)
pages = {
    "recipes.md": render.render_recipes_page,
    "ingredients.md": render.render_ingredients_page,
    "grocery-list.md": render.render_grocery_page,
    "meal-plan.md": render.render_meal_plan_page,
}
for name, fn in pages.items():
    with open(os.path.join(OUT, name), "w") as f:
        f.write(fn() + "\n")
print("wrote", len(pages), "preview pages to", OUT)
