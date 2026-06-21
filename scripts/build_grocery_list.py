#!/usr/bin/env python3
"""CLI: print/write the weekly grocery list from data/meal_plan.yaml.

Thin wrapper over the shared core (proteinplate.render.render_grocery_page),
so the terminal output and the website page are byte-identical.

Usage:  uv run python scripts/build_grocery_list.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from proteinplate import render  # noqa: E402

if __name__ == "__main__":
    md = render.render_grocery_page()
    out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "data", "sample_grocery_list.md")
    with open(out, "w") as f:
        f.write(md + "\n")
    print(md)
    print(f"\n[written to {out}]")
