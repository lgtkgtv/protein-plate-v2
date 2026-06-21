# Recipe data schema

This is the **single source of truth** for ProteinPlate recipes. The website,
the grocery-list builder, a future PWA, and any app all render from these files
instead of re-implementing the content. Change a recipe here, and every surface
updates.

```
data/
  ingredients.yaml        # canonical ingredient registry (grocery aisle, aliases, macros)
  recipes/<id>.yaml       # one file per recipe  (20 today)
schema/
  recipe.schema.json      # the machine-enforced contract (JSON Schema 2020-12)
scripts/
  validate.py             # schema + cross-reference checks  (CI gate)
  build_grocery_list.py   # aggregates a meal plan -> categorised checklist
  bootstrap_import.py      # one-time import from the website prose (do not re-run)
```

## Why YAML, why two files

- **YAML for authoring** — contributors edit plain text, matching the project's
  "markdown-first" philosophy. No HTML, no build step to add a recipe.
- **A registry, not repeated metadata** — `ingredients.yaml` holds each
  ingredient's grocery aisle, aliases, "buy X to make Y" mapping, and (later)
  macros *once*. Recipes reference ingredients by id. This is what makes the
  grocery list aggregate correctly and keeps macros consistent. Without it,
  "onion" would carry its aisle in 11 different files and drift out of sync.

## Recipe fields

| Field                | Req | Notes                                                                 |
|----------------------|-----|-----------------------------------------------------------------------|
| `id`                 | yes | slug; must equal the filename                                         |
| `name`               | yes | display name                                                          |
| `category`           | yes | `protein-anchor` \| `binder` \| `side` \| `salad` \| `condiment`      |
| `protein_family`     | —   | `sprouts-legumes` \| `paneer` \| `eggs` \| `chicken` \| `binder`      |
| `base_servings`      | yes | the reference for scaling (usually 4)                                  |
| `batch`              | —   | true for jar/batch items (e.g. toasted nuts)                          |
| `serving_note`       | —   | e.g. "~25 g per person"                                               |
| `tags`               | —   | free-form filters (`high-protein`, `no-cook`, `batch-friendly`, …)    |
| `time`               | —   | `prep_min`, `marinate_min`, `cook_min`                                |
| `diet`               | —   | booleans: `vegetarian`, `vegan`, `egg`, `gluten_free`, `no_cook`      |
| `ingredients`        | yes | list; see below                                                       |
| `steps`              | yes | ordered list of strings                                               |
| `storage`            | —   | `fridge_days`, `freezer_days`, `note`                                 |
| `media`              | —   | `video`, `image`                                                      |
| `tips`               | —   | list of strings                                                       |
| `macros_per_serving` | —   | `kcal`, `protein_g`, `carbs_g`, `fat_g`, `source`, `verified`         |
| `source_note`        | —   | provenance                                                            |

### Ingredient line

```yaml
- item: boneless-chicken   # must exist in ingredients.yaml
  qty: 900                 # number, or null for "to taste"
  unit: g                  # g kg ml l tsp tbsp cup piece clove sprig bunch
                           #   handful head pinch to_taste to_cover as_needed
  prep: cubed              # optional
  scale: true              # optional, default true; false = fixed (spices, "to taste")
  optional: false          # optional
```

`scale: false` matters: in v1 the serving-scaler multiplies numeric quantities
**linearly**, which is right for proteins and vegetables but wrong for spices,
oil and salt. Marking those `scale: false` keeps a 2-person plate from getting
double the chilli. Spice scaling curves are a deliberate future refinement.

## On macros (important)

Every `macros_*` block is present but **null / `verified: false`**. We do **not**
invent nutrition numbers. The macro pass will pull per-100g values from a cited
source (USDA FoodData Central, or IFCT 2017 for Indian foods), compute per
serving, and mark `verified: true` only after a human checks them. This keeps a
health-adjacent project honest. The schema is ready to receive them today.

## Extension roadmap (intentionally not in v1)

1. **Unit normalisation** — the grocery builder currently lists the same item
   once per unit (e.g. oil in both tbsp and tsp) because it never adds unlikes.
   A small conversion table (tsp→tbsp→cup, g↔kg, and density for cup↔g of known
   items) collapses these. Correct-but-verbose now; tidy later.
2. **Component composition** — the onion-tomato masala base is currently inlined
   in chana / bhurji / egg-bhurji. A `uses: [masala-base]` reference with
   recursive expansion would model "one base, many meals" in data. Kept inline
   in v1 so grocery aggregation needs no recursion.
3. **i18n** — keep `name`/`steps` translatable; a parallel `i18n/<lang>/<id>.yaml`
   overlay avoids forking the data.
4. **Macro pass** — as above.

## Working with the data

```bash
uv sync
uv run python scripts/validate.py            # gate every change
uv run python scripts/build_grocery_list.py  # see the aggregation
```

Adding a recipe: copy an existing `data/recipes/*.yaml`, edit it, ensure any new
ingredient exists in `ingredients.yaml`, then run `validate.py`.
