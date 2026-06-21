#!/usr/bin/env python3
"""
ONE-TIME BOOTSTRAP — imports the recipes from the ProteinPlate website prose
into structured YAML data files.

After this runs, the files under data/recipes/*.yaml and data/ingredients.yaml
are the CANONICAL source of truth. Contributors edit the YAML directly.
Do NOT re-run this to "regenerate" — it would overwrite hand edits.

Notes on fidelity:
  - Quantities that were vague in the source prose (e.g. "turmeric, chilli")
    were normalised to typical home-cooking amounts and should be reviewed.
  - macros_per_serving / macros_per_100g are intentionally left null. They will
    be filled in a later, source-verified pass (USDA FDC / IFCT) with a human
    in the loop — we do not invent health numbers.
"""
import os
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RECIPE_DIR = os.path.join(ROOT, "data", "recipes")
ING_FILE = os.path.join(ROOT, "data", "ingredients.yaml")

# ---------------------------------------------------------------------------
# Canonical ingredient registry.
#  id -> (display, grocery_category, purchase_as, purchase_note, aliases)
# grocery_category drives how the shopping list is grouped.
# purchase_as / purchase_note capture the "buy X to make Y" real-world mapping.
# ---------------------------------------------------------------------------
GROCERY_CATEGORIES = [
    "produce", "protein-dairy", "nuts-seeds", "flour",
    "fat-oil", "pantry-spice", "condiment-other", "skip",
]

# (id, display, category, purchase_as, purchase_note, aliases)
INGREDIENTS = [
    # --- produce ---------------------------------------------------------
    ("onion", "Onion", "produce", None, None, []),
    ("tomato", "Tomato", "produce", None, None, []),
    ("cherry-tomato", "Cherry tomato", "produce", None, None, []),
    ("green-chilli", "Green chilli", "produce", None, None, []),
    ("capsicum", "Bell pepper / capsicum", "produce", None, None, ["bell pepper"]),
    ("broccoli", "Broccoli", "produce", None, None, []),
    ("mushroom", "Mushroom", "produce", None, None, []),
    ("cabbage", "Cabbage", "produce", None, None, []),
    ("cucumber", "Cucumber", "produce", None, None, []),
    ("carrot", "Carrot", "produce", None, None, []),
    ("spinach", "Spinach", "produce", None, None, ["palak"]),
    ("methi", "Fenugreek greens (methi)", "produce", None, None, []),
    ("lettuce", "Lettuce", "produce", None, None, []),
    ("green-beans", "Green beans", "produce", None, None, []),
    ("bottle-gourd", "Bottle gourd (lauki)", "produce", None, None, ["lauki"]),
    ("avocado", "Avocado", "produce", None, None, []),
    ("lemon", "Lemon / lime", "produce", None, None, ["lime"]),
    ("garlic", "Garlic", "produce", None, None, []),
    ("ginger", "Ginger", "produce", None, None, []),
    ("ginger-garlic-paste", "Ginger-garlic paste", "produce", None,
     "Buy a jar, or blend fresh ginger + garlic.", []),
    ("coriander-fresh", "Coriander (fresh)", "produce", None, None, ["cilantro"]),
    ("mint", "Mint (fresh)", "produce", None, None, ["pudina"]),
    ("curry-leaves", "Curry leaves", "produce", None, None, []),
    # --- protein & dairy -------------------------------------------------
    ("paneer", "Paneer", "protein-dairy", None, None, []),
    ("eggs", "Eggs", "protein-dairy", None, None, []),
    ("boneless-chicken", "Boneless chicken", "protein-dairy", None, None,
     ["chicken breast", "chicken thigh"]),
    ("curd", "Curd / yogurt", "protein-dairy", None, None, ["yogurt", "dahi"]),
    ("milk", "Milk", "protein-dairy", None, None, []),
    ("moong-sprouts", "Moong sprouts", "protein-dairy", "green-moong-dry",
     "Buy dry green moong and sprout at home — sprouting ~triples the volume.",
     []),
    ("boiled-chickpeas", "Boiled chickpeas / chana", "protein-dairy",
     "chickpea-dry", "Buy dry chana (cheapest) or canned chickpeas.", []),
    # --- nuts & seeds ----------------------------------------------------
    ("almonds", "Almonds", "nuts-seeds", None, None, []),
    ("walnuts", "Walnuts", "nuts-seeds", None, None, []),
    ("cashews", "Cashews", "nuts-seeds", None, None, []),
    ("pumpkin-seeds", "Pumpkin seeds", "nuts-seeds", None, None, []),
    ("sunflower-seeds", "Sunflower seeds", "nuts-seeds", None, None, []),
    ("flax-seeds", "Flax seeds", "nuts-seeds", None, None, []),
    ("mixed-seeds", "Mixed seeds", "nuts-seeds", None,
     "Pumpkin + sunflower + flax mix.", []),
    ("nuts-mixed", "Mixed nuts", "nuts-seeds", None, None, []),
    # --- flours & dals ---------------------------------------------------
    ("besan", "Besan (gram flour)", "flour", None, None, ["gram flour"]),
    ("moong-dal", "Moong dal", "flour", None, None, []),
    ("oats", "Oats / daliya", "flour", None, None, []),
    ("sattu", "Sattu (roasted gram flour)", "flour", None, None, []),
    # --- fats & oils -----------------------------------------------------
    ("oil", "Cooking oil (groundnut/mustard)", "fat-oil", None, None, []),
    ("olive-oil", "Olive oil", "fat-oil", None, None, []),
    ("ghee", "Ghee", "fat-oil", None, None, []),
    # --- pantry & spices -------------------------------------------------
    ("mustard-seeds", "Mustard seeds", "pantry-spice", None, None, []),
    ("cumin-seeds", "Cumin seeds (jeera)", "pantry-spice", None, None, []),
    ("cumin-powder", "Cumin powder", "pantry-spice", None, None, []),
    ("turmeric", "Turmeric", "pantry-spice", None, None, ["haldi"]),
    ("red-chilli-powder", "Red chilli powder", "pantry-spice", None, None, []),
    ("kashmiri-chilli-powder", "Kashmiri chilli powder", "pantry-spice", None, None, []),
    ("coriander-powder", "Coriander powder", "pantry-spice", None, None, []),
    ("garam-masala", "Garam masala", "pantry-spice", None, None, []),
    ("chaat-masala", "Chaat masala", "pantry-spice", None, None, []),
    ("amchur", "Amchur (dry mango powder)", "pantry-spice", None, None, []),
    ("kasuri-methi", "Kasuri methi (dried fenugreek)", "pantry-spice", None, None, []),
    ("ajwain", "Ajwain (carom seeds)", "pantry-spice", None, None, []),
    ("black-pepper", "Black pepper", "pantry-spice", None, None, []),
    ("chilli-flakes", "Chilli flakes", "pantry-spice", None, None, []),
    ("salt", "Salt", "pantry-spice", None, None, []),
    ("hing", "Hing (asafoetida)", "pantry-spice", None, None, []),
    ("bay-leaf", "Bay leaf", "pantry-spice", None, None, []),
    # --- condiments / other ---------------------------------------------
    ("tahini", "Tahini (sesame paste)", "condiment-other", None, None, []),
    # --- skip in grocery -------------------------------------------------
    ("water", "Water", "skip", None, None, []),
]


def build_registry():
    reg = {}
    for iid, display, cat, purchase_as, note, aliases in INGREDIENTS:
        entry = {"display": display, "grocery_category": cat}
        if purchase_as:
            entry["purchase_as"] = purchase_as
        if note:
            entry["purchase_note"] = note
        if aliases:
            entry["aliases"] = aliases
        # macro slot, to be filled by a verified pass later
        entry["macros_per_100g"] = {
            "kcal": None, "protein_g": None, "carbs_g": None,
            "fat_g": None, "source": None, "verified": False,
        }
        reg[iid] = entry
    return reg


# ---------------------------------------------------------------------------
# Recipe helpers
# ---------------------------------------------------------------------------
def ing(item, qty, unit, prep=None, scale=True, optional=False):
    d = {"item": item, "qty": qty, "unit": unit}
    if prep:
        d["prep"] = prep
    if not scale:
        d["scale"] = False
    if optional:
        d["optional"] = True
    return d


def recipe(**kw):
    """Assemble a recipe dict in a fixed, readable field order."""
    order = [
        "id", "name", "category", "protein_family", "base_servings",
        "batch", "serving_note", "tags", "time", "diet",
        "ingredients", "steps", "storage", "media", "tips",
        "macros_per_serving", "source_note",
    ]
    out = {}
    for k in order:
        if k in kw and kw[k] not in (None, [], {}):
            out[k] = kw[k]
    # always include an (empty) macro slot so the field exists everywhere
    out["macros_per_serving"] = kw.get("macros_per_serving", {
        "kcal": None, "protein_g": None, "carbs_g": None,
        "fat_g": None, "source": None, "verified": False,
    })
    return out


def diet(vegetarian=False, vegan=False, egg=False, gluten_free=False, no_cook=False):
    return {
        "vegetarian": vegetarian, "vegan": vegan, "egg": egg,
        "gluten_free": gluten_free, "no_cook": no_cook,
    }


RECIPES = []

# 1. Moong sprouts usal
RECIPES.append(recipe(
    id="moong-sprouts-usal", name="Moong sprouts usal",
    category="protein-anchor", protein_family="sprouts-legumes", base_servings=4,
    tags=["high-protein", "vegan", "gluten-free"],
    time={"prep_min": 10, "cook_min": 15},
    diet=diet(vegetarian=True, vegan=True, gluten_free=True),
    ingredients=[
        ing("moong-sprouts", 3, "cup"),
        ing("onion", 1, "piece", "chopped"),
        ing("tomato", 1, "piece", "chopped"),
        ing("ginger-garlic-paste", 1, "tsp"),
        ing("green-chilli", 1, "piece", "slit"),
        ing("mustard-seeds", 1, "tsp", scale=False),
        ing("cumin-seeds", 1, "tsp", scale=False),
        ing("turmeric", 0.5, "tsp", scale=False),
        ing("red-chilli-powder", 1, "tsp", scale=False),
        ing("curry-leaves", 1, "sprig", optional=True),
        ing("oil", 1, "tbsp"),
        ing("salt", None, "to_taste", scale=False),
        ing("coriander-fresh", 2, "tbsp", "chopped", optional=True),
        ing("lemon", 0.5, "piece", optional=True),
        ing("water", 0.5, "cup", scale=False),
    ],
    steps=[
        "Heat oil; splutter mustard + cumin, add curry leaves, onion, ginger-garlic and chilli — saute till golden.",
        "Add tomato + dry spices; cook till soft.",
        "Add sprouts + 1/2 cup water, cover, simmer 8-10 min (keep some crunch).",
        "Finish with coriander and a squeeze of lemon.",
    ],
    storage={"fridge_days": 3, "freezer_days": None, "note": None},
    media={"video": "https://www.youtube.com/watch?v=u33FYQVfZ68"},
    tips=["Steam sprouts first for a softer texture."],
))

# 2. Chana / chickpea masala
RECIPES.append(recipe(
    id="chana-masala", name="Chana / chickpea masala",
    category="protein-anchor", protein_family="sprouts-legumes", base_servings=4,
    tags=["high-protein", "vegan", "gluten-free", "batch-friendly"],
    time={"prep_min": 10, "cook_min": 20},
    diet=diet(vegetarian=True, vegan=True, gluten_free=True),
    ingredients=[
        ing("boiled-chickpeas", 3, "cup"),
        ing("onion", 2, "piece", "chopped"),
        ing("tomato", 2, "piece", "pureed"),
        ing("ginger-garlic-paste", 1, "tbsp"),
        ing("turmeric", 0.5, "tsp", scale=False),
        ing("red-chilli-powder", 1, "tsp", scale=False),
        ing("coriander-powder", 1, "tsp", scale=False),
        ing("cumin-powder", 1, "tsp", scale=False),
        ing("garam-masala", 1, "tsp", scale=False),
        ing("amchur", 0.5, "tsp", scale=False),
        ing("oil", 2, "tbsp"),
        ing("salt", None, "to_taste", scale=False),
        ing("coriander-fresh", 2, "tbsp", "chopped", optional=True),
        ing("water", 1, "cup", scale=False),
    ],
    steps=[
        "Saute onion till deep golden; add ginger-garlic, then tomato puree + spices; cook till oil separates.",
        "Add chickpeas + 1 cup water; simmer 10-15 min; mash a few to thicken.",
        "Finish with garam masala, amchur and coriander.",
    ],
    storage={"fridge_days": 5, "freezer_days": 30, "note": None},
    media={"video": "https://www.indianhealthyrecipes.com/chana-masala/"},
    tips=["Make a double batch of the onion-tomato masala base and freeze it — "
          "it becomes the base for chana, paneer or egg dishes in minutes."],
))

# 3. Grilled paneer on tawa
RECIPES.append(recipe(
    id="grilled-paneer-tawa", name="Grilled paneer on tawa",
    category="protein-anchor", protein_family="paneer", base_servings=4,
    tags=["high-protein", "vegetarian", "gluten-free"],
    time={"prep_min": 10, "marinate_min": 30, "cook_min": 12},
    diet=diet(vegetarian=True, gluten_free=True),
    ingredients=[
        ing("paneer", 500, "g", "cubed or sliced"),
        ing("curd", 0.5, "cup", "thick"),
        ing("red-chilli-powder", 1, "tsp", scale=False),
        ing("turmeric", 0.5, "tsp", scale=False),
        ing("garam-masala", 0.5, "tsp", scale=False),
        ing("chaat-masala", 0.5, "tsp", scale=False),
        ing("kasuri-methi", 0.5, "tsp", scale=False),
        ing("besan", 2, "tsp", "roasted", scale=False),
        ing("lemon", 1, "tbsp"),
        ing("ginger-garlic-paste", 1, "tsp"),
        ing("oil", 1, "tsp"),
        ing("salt", None, "to_taste", scale=False),
    ],
    steps=[
        "Whisk the marinade; coat paneer; rest 30 min (no longer — acid makes paneer rubbery).",
        "Sear on a medium-high, lightly oiled tawa 3-4 min per side until charred. Don't move it constantly.",
    ],
    storage={"fridge_days": None, "freezer_days": None,
             "note": "Cook fresh for best texture."},
    media={"video": "https://www.youtube.com/watch?v=BwIJHI4KdIE"},
    tips=["Sear marinated capsicum and onion alongside."],
))

# 4. Paneer bhurji
RECIPES.append(recipe(
    id="paneer-bhurji", name="Paneer bhurji",
    category="protein-anchor", protein_family="paneer", base_servings=4,
    tags=["high-protein", "vegetarian", "gluten-free"],
    time={"prep_min": 10, "cook_min": 12},
    diet=diet(vegetarian=True, gluten_free=True),
    ingredients=[
        ing("paneer", 500, "g", "crumbled"),
        ing("onion", 2, "piece", "chopped"),
        ing("tomato", 2, "piece", "chopped"),
        ing("capsicum", 1, "piece", "chopped"),
        ing("green-chilli", 1, "piece", "chopped"),
        ing("ginger-garlic-paste", 1, "tsp"),
        ing("turmeric", 0.5, "tsp", scale=False),
        ing("red-chilli-powder", 1, "tsp", scale=False),
        ing("garam-masala", 0.5, "tsp", scale=False),
        ing("oil", 1, "tbsp"),
        ing("salt", None, "to_taste", scale=False),
        ing("coriander-fresh", 2, "tbsp", "chopped", optional=True),
    ],
    steps=[
        "Saute onion -> ginger-garlic -> capsicum -> tomato + spices till soft.",
        "Add crumbled paneer, toss 3-4 min, finish with coriander.",
    ],
    storage={"fridge_days": 2, "freezer_days": None, "note": None},
    media={},
    tips=["Same recipe with eggs instead of paneer = egg bhurji."],
))

# 5. Boiled eggs
RECIPES.append(recipe(
    id="boiled-eggs", name="Boiled eggs",
    category="protein-anchor", protein_family="eggs", base_servings=4,
    tags=["high-protein", "gluten-free", "egg"],
    time={"prep_min": 1, "cook_min": 9},
    diet=diet(egg=True, gluten_free=True),
    ingredients=[
        ing("eggs", 8, "piece"),
        ing("water", None, "to_cover", scale=False),
    ],
    steps=[
        "Cover eggs with water, boil 8-9 min.",
        "Ice-bath, then peel.",
    ],
    storage={"fridge_days": 7, "freezer_days": None,
             "note": "Keep in shell, fridge 5-7 days."},
    media={},
    tips=["2 eggs per person is a typical serving."],
))

# 6. Vegetable omelette
RECIPES.append(recipe(
    id="vegetable-omelette", name="Vegetable omelette",
    category="protein-anchor", protein_family="eggs", base_servings=4,
    tags=["high-protein", "gluten-free", "egg"],
    time={"prep_min": 8, "cook_min": 8},
    diet=diet(egg=True, gluten_free=True),
    ingredients=[
        ing("eggs", 8, "piece"),
        ing("onion", 1, "piece", "chopped"),
        ing("tomato", 1, "piece", "chopped"),
        ing("capsicum", 1, "piece", "chopped"),
        ing("spinach", 1, "handful", "chopped"),
        ing("green-chilli", 1, "piece", "chopped"),
        ing("turmeric", 0.25, "tsp", scale=False),
        ing("salt", None, "to_taste", scale=False),
        ing("ghee", 0.5, "tsp"),
    ],
    steps=[
        "Beat eggs with chopped vegetables, chilli, salt and turmeric.",
        "Cook on a little ghee, flip once.",
    ],
    storage={"fridge_days": None, "freezer_days": None, "note": "Cook fresh."},
    media={},
    tips=[],
))

# 7. Egg bhurji
RECIPES.append(recipe(
    id="egg-bhurji", name="Egg bhurji",
    category="protein-anchor", protein_family="eggs", base_servings=4,
    tags=["high-protein", "gluten-free", "egg"],
    time={"prep_min": 8, "cook_min": 10},
    diet=diet(egg=True, gluten_free=True),
    ingredients=[
        ing("eggs", 8, "piece", "beaten"),
        ing("onion", 2, "piece", "chopped"),
        ing("tomato", 2, "piece", "chopped"),
        ing("green-chilli", 1, "piece", "chopped"),
        ing("ginger-garlic-paste", 1, "tsp"),
        ing("turmeric", 0.5, "tsp", scale=False),
        ing("red-chilli-powder", 1, "tsp", scale=False),
        ing("garam-masala", 0.5, "tsp", scale=False),
        ing("oil", 1, "tbsp"),
        ing("salt", None, "to_taste", scale=False),
        ing("coriander-fresh", 2, "tbsp", "chopped", optional=True),
    ],
    steps=[
        "Build the onion-tomato masala base; cook till soft.",
        "Pour beaten eggs at the end; scramble on medium-low (high heat = rubbery).",
        "Pull off heat while slightly underdone.",
    ],
    storage={"fridge_days": 2, "freezer_days": None, "note": None},
    media={"video": "https://www.youtube.com/watch?v=1OdPf65aPJg"},
    tips=["Reuse the same masala base from chana for a fast meal."],
))

# 8. Chicken tikka on tawa
RECIPES.append(recipe(
    id="chicken-tikka-tawa", name="Chicken tikka on tawa",
    category="protein-anchor", protein_family="chicken", base_servings=4,
    tags=["high-protein", "gluten-free", "batch-friendly"],
    time={"prep_min": 15, "marinate_min": 60, "cook_min": 20},
    diet=diet(gluten_free=True),
    ingredients=[
        ing("boneless-chicken", 900, "g", "cubed"),
        ing("curd", 0.75, "cup", "hung"),
        ing("ginger-garlic-paste", 1.5, "tbsp"),
        ing("lemon", 2, "tbsp"),
        ing("kashmiri-chilli-powder", 1.5, "tsp", scale=False),
        ing("turmeric", 0.5, "tsp", scale=False),
        ing("garam-masala", 1, "tsp", scale=False),
        ing("chaat-masala", 1, "tsp", scale=False),
        ing("kasuri-methi", 1, "tsp", scale=False),
        ing("besan", 2, "tbsp", "roasted", scale=False),
        ing("oil", 1, "tbsp"),
        ing("salt", None, "to_taste", scale=False),
    ],
    steps=[
        "First marinade: chicken + lemon + ginger-garlic + salt, 30 min.",
        "Second marinade: add hung curd + spices + besan + oil; rest 1 hr, ideally overnight.",
        "Sear on a hot tawa/cast-iron, single layer, 4-5 min per side until charred and "
        "cooked through (no pink, ~75 C internal). Work in batches.",
    ],
    storage={"fridge_days": 3, "freezer_days": 30,
             "note": "Freeze raw in marinade up to 1 month (thaw overnight); cooked keeps 3 days."},
    media={"video": "https://www.youtube.com/watch?v=8L7V1eTaTnw"},
    tips=["Hung curd makes the chicken sear instead of steam."],
))

# 9. Chicken-vegetable stir-fry
RECIPES.append(recipe(
    id="chicken-veg-stirfry", name="Chicken-vegetable stir-fry",
    category="protein-anchor", protein_family="chicken", base_servings=4,
    tags=["high-protein", "gluten-free"],
    time={"prep_min": 15, "cook_min": 15},
    diet=diet(gluten_free=True),
    ingredients=[
        ing("boneless-chicken", 700, "g", "cubed"),
        ing("broccoli", 200, "g", "florets"),
        ing("capsicum", 1, "piece", "sliced"),
        ing("cabbage", 100, "g", "shredded"),
        ing("onion", 1, "piece", "sliced"),
        ing("cucumber", 1, "piece", "sliced"),
        ing("ginger-garlic-paste", 1, "tbsp"),
        ing("black-pepper", 1, "tsp", scale=False),
        ing("chilli-flakes", 1, "tsp", scale=False),
        ing("oil", 1, "tbsp"),
        ing("salt", None, "to_taste", scale=False),
    ],
    steps=[
        "Sear chicken first till golden, remove.",
        "Stir-fry hard veg on high 3-4 min, then quick-cooking veg.",
        "Return chicken; toss with pepper, chilli flakes and salt.",
    ],
    storage={"fridge_days": 3, "freezer_days": None, "note": None},
    media={"image": "assets/images/05-chicken-veg-stirfry.jpeg"},
    tips=["High heat + don't crowd the pan = sear, not steam."],
))

# 10. Besan / moong cheela
RECIPES.append(recipe(
    id="besan-moong-cheela", name="Besan / moong cheela",
    category="binder", protein_family="binder", base_servings=4,
    tags=["high-protein", "vegetarian", "gluten-free"],
    time={"prep_min": 10, "cook_min": 20},
    diet=diet(vegetarian=True, vegan=True, gluten_free=True),
    ingredients=[
        ing("besan", 2, "cup"),
        ing("onion", 1, "piece", "finely chopped"),
        ing("tomato", 1, "piece", "finely chopped"),
        ing("capsicum", 0.5, "piece", "finely chopped"),
        ing("coriander-fresh", 1, "handful", "chopped"),
        ing("green-chilli", 1, "piece", "chopped"),
        ing("ajwain", 0.5, "tsp", scale=False),
        ing("turmeric", 0.25, "tsp", scale=False),
        ing("salt", None, "to_taste", scale=False),
        ing("oil", 2, "tsp"),
        ing("water", None, "as_needed", scale=False),
    ],
    steps=[
        "Mix besan, vegetables and spices with water to a pourable batter; rest 10 min.",
        "On a hot tawa pour a ladle, spread thin, drizzle oil, flip when edges lift.",
        "Serve with green chutney.",
    ],
    storage={"fridge_days": None, "freezer_days": None, "note": "Cook fresh."},
    media={"video": "https://www.youtube.com/watch?v=8qUJOvPkpl8"},
    tips=["Add 2-3 tbsp sattu or crumbled paneer to push protein higher.",
          "Alternative base: 1.5 cups soaked-and-ground moong dal instead of besan."],
))

# 11. Sauteed mixed vegetables
RECIPES.append(recipe(
    id="sauteed-mixed-vegetables", name="Sauteed mixed vegetables",
    category="side", base_servings=4,
    tags=["vegetarian", "vegan", "gluten-free", "low-cal"],
    time={"prep_min": 8, "cook_min": 10},
    diet=diet(vegetarian=True, vegan=True, gluten_free=True),
    ingredients=[
        ing("broccoli", 200, "g", "florets"),
        ing("capsicum", 1, "piece", "sliced"),
        ing("mushroom", 150, "g", "sliced"),
        ing("onion", 1, "piece", "sliced"),
        ing("garlic", 2, "clove", "chopped"),
        ing("mixed-seeds", 1, "tbsp"),
        ing("oil", 1, "tbsp"),
        ing("salt", None, "to_taste", scale=False),
    ],
    steps=[
        "Hot pan: garlic + onion 1 min -> broccoli + capsicum 3-4 min -> mushroom 2 min.",
        "Season; finish with mixed seeds. Keep it crisp-tender.",
    ],
    storage={"fridge_days": 2, "freezer_days": None, "note": None},
    media={"image": "assets/images/06-grilled-chicken-sauteed-veg.jpeg"},
    tips=[],
))

# 12. Sauteed greens / bean sabzi
RECIPES.append(recipe(
    id="sauteed-greens-bean-sabzi", name="Sauteed greens / bean sabzi",
    category="side", base_servings=4,
    tags=["vegetarian", "vegan", "gluten-free", "low-cal"],
    time={"prep_min": 8, "cook_min": 10},
    diet=diet(vegetarian=True, vegan=True, gluten_free=True),
    ingredients=[
        ing("spinach", 250, "g", "chopped"),
        ing("garlic", 2, "clove", "chopped"),
        ing("red-chilli-powder", 0.5, "tsp", scale=False),
        ing("mustard-seeds", 0.5, "tsp", scale=False, optional=True),
        ing("cumin-seeds", 0.5, "tsp", scale=False, optional=True),
        ing("oil", 1, "tbsp"),
        ing("salt", None, "to_taste", scale=False),
    ],
    steps=[
        "Greens version: garlic + spinach/methi wilted 2-3 min with salt and chilli.",
        "Bean version: beans/capsicum with mustard-cumin tempering, 6-8 min covered.",
    ],
    storage={"fridge_days": 2, "freezer_days": None, "note": None},
    media={},
    tips=["Swap spinach for methi, green beans or capsicum using the same method."],
))

# 13. Green soup
RECIPES.append(recipe(
    id="green-soup", name="Green soup",
    category="side", base_servings=4,
    tags=["vegetarian", "gluten-free", "low-cal", "batch-friendly"],
    time={"prep_min": 8, "cook_min": 12},
    diet=diet(vegetarian=True, gluten_free=True),
    ingredients=[
        ing("bottle-gourd", 1, "piece", "chopped"),
        ing("onion", 1, "piece", "chopped"),
        ing("garlic", 2, "clove"),
        ing("black-pepper", None, "to_taste", scale=False),
        ing("salt", None, "to_taste", scale=False),
        ing("curd", 1, "tbsp", optional=True),
        ing("water", 3, "cup", scale=False),
    ],
    steps=[
        "Boil chopped lauki (or spinach/broccoli) with onion + garlic till soft (~10 min).",
        "Blend, season with pepper and salt, finish with a spoon of curd or milk.",
    ],
    storage={"fridge_days": 3, "freezer_days": 30, "note": None},
    media={},
    tips=["Make a big batch — it freezes well."],
))

# 14. Kachumber
RECIPES.append(recipe(
    id="kachumber", name="Kachumber salad",
    category="salad", base_servings=4,
    tags=["vegetarian", "vegan", "gluten-free", "no-cook", "low-cal"],
    time={"prep_min": 8},
    diet=diet(vegetarian=True, vegan=True, gluten_free=True, no_cook=True),
    ingredients=[
        ing("tomato", 1, "piece", "diced"),
        ing("cucumber", 1, "piece", "diced"),
        ing("onion", 1, "piece", "diced"),
        ing("coriander-fresh", 1, "tbsp", "chopped"),
        ing("lemon", 0.5, "piece"),
        ing("chaat-masala", 0.5, "tsp", scale=False),
    ],
    steps=["Combine equal tomato, cucumber and onion with coriander, lemon and chaat masala.",
           "Dress just before eating."],
    storage={"fridge_days": None, "freezer_days": None, "note": "Eat fresh."},
    media={},
    tips=["Salt/dress last — salt pulls out water and makes it soggy."],
))

# 15. Curd vegetable raita
RECIPES.append(recipe(
    id="curd-vegetable-raita", name="Curd vegetable salad / raita",
    category="salad", base_servings=4,
    tags=["vegetarian", "gluten-free", "no-cook"],
    time={"prep_min": 6},
    diet=diet(vegetarian=True, gluten_free=True, no_cook=True),
    ingredients=[
        ing("curd", 1, "cup", "whisked"),
        ing("tomato", 0.5, "piece", "diced"),
        ing("cucumber", 0.5, "piece", "diced"),
        ing("onion", 0.5, "piece", "diced"),
        ing("cumin-powder", 0.5, "tsp", "roasted", scale=False),
        ing("salt", None, "to_taste", scale=False),
        ing("coriander-fresh", 1, "tbsp", "chopped", optional=True),
    ],
    steps=["Fold diced vegetables into whisked curd with roasted cumin and salt."],
    storage={"fridge_days": 1, "freezer_days": None, "note": None},
    media={},
    tips=[],
))

# 16. Big leafy salad
RECIPES.append(recipe(
    id="big-leafy-salad", name="Big leafy salad",
    category="salad", base_servings=4,
    tags=["vegetarian", "vegan", "gluten-free", "no-cook", "low-cal"],
    time={"prep_min": 10},
    diet=diet(vegetarian=True, vegan=True, gluten_free=True, no_cook=True),
    ingredients=[
        ing("lettuce", 1, "head", "torn"),
        ing("cabbage", 100, "g", "shredded"),
        ing("spinach", 1, "handful"),
        ing("broccoli", 100, "g", "small florets"),
        ing("capsicum", 1, "piece", "sliced"),
        ing("cherry-tomato", 100, "g"),
        ing("mixed-seeds", 1, "tbsp"),
        ing("nuts-mixed", 1, "tbsp"),
        ing("lemon", 0.5, "piece"),
        ing("olive-oil", 1, "tbsp"),
    ],
    steps=["Toss leaves and vegetables; top with seeds and nuts; dress with lemon + olive oil."],
    storage={"fridge_days": None, "freezer_days": None, "note": "Dress just before eating."},
    media={},
    tips=["Store washed-and-dried greens with a paper towel in an airtight box; "
          "moisture is what makes salad slimy."],
))

# 17. Hummus
RECIPES.append(recipe(
    id="hummus", name="Hummus",
    category="condiment", base_servings=6,
    tags=["vegetarian", "vegan", "gluten-free", "batch-friendly"],
    time={"prep_min": 10},
    diet=diet(vegetarian=True, vegan=True, gluten_free=True),
    ingredients=[
        ing("boiled-chickpeas", 1.5, "cup"),
        ing("tahini", 2, "tbsp"),
        ing("garlic", 1, "clove"),
        ing("lemon", 2, "tbsp"),
        ing("olive-oil", 2, "tbsp"),
        ing("cumin-powder", 0.5, "tsp", scale=False),
        ing("salt", None, "to_taste", scale=False),
        ing("water", None, "as_needed", scale=False),
    ],
    steps=["Blend boiled chickpeas + tahini + garlic + lemon + olive oil + salt + cumin "
           "with a little water until smooth."],
    storage={"fridge_days": 5, "freezer_days": None, "note": None},
    media={},
    tips=[],
))

# 18. Green chutney
RECIPES.append(recipe(
    id="green-chutney", name="Green chutney",
    category="condiment", base_servings=8,
    tags=["vegetarian", "vegan", "gluten-free", "batch-friendly"],
    time={"prep_min": 8},
    diet=diet(vegetarian=True, vegan=True, gluten_free=True, no_cook=True),
    ingredients=[
        ing("coriander-fresh", 1, "cup"),
        ing("mint", 0.5, "cup"),
        ing("green-chilli", 1, "piece"),
        ing("ginger", 1, "tsp"),
        ing("lemon", 0.5, "piece"),
        ing("salt", None, "to_taste", scale=False),
    ],
    steps=["Blend coriander + mint + green chilli + ginger + lemon + salt to a smooth chutney."],
    storage={"fridge_days": 4, "freezer_days": 30,
             "note": "Freezes well in ice-cube trays."},
    media={},
    tips=[],
))

# 19. Buttermilk / chaas
RECIPES.append(recipe(
    id="buttermilk-chaas", name="Buttermilk (chaas)",
    category="condiment", base_servings=4,
    tags=["vegetarian", "gluten-free", "no-cook"],
    time={"prep_min": 4},
    diet=diet(vegetarian=True, gluten_free=True, no_cook=True),
    ingredients=[
        ing("curd", 0.5, "cup"),
        ing("water", 1.5, "cup", scale=False),
        ing("cumin-powder", 0.25, "tsp", "roasted", scale=False),
        ing("salt", None, "to_taste", scale=False),
        ing("coriander-fresh", 1, "tbsp", "chopped", optional=True),
    ],
    steps=["Whisk curd + water + roasted cumin + salt + coriander until frothy."],
    storage={"fridge_days": 1, "freezer_days": None, "note": None},
    media={},
    tips=[],
))

# 20. Toasted nuts & seeds
RECIPES.append(recipe(
    id="toasted-nuts-seeds", name="Toasted nuts & seeds",
    category="condiment", base_servings=30, batch=True,
    serving_note="~25 g per person.",
    tags=["vegetarian", "vegan", "gluten-free", "batch-friendly"],
    time={"prep_min": 2, "cook_min": 8},
    diet=diet(vegetarian=True, vegan=True, gluten_free=True),
    ingredients=[
        ing("almonds", 250, "g"),
        ing("walnuts", 250, "g"),
        ing("pumpkin-seeds", 200, "g"),
        ing("sunflower-seeds", 150, "g"),
    ],
    steps=["Dry-toast nuts and seeds in batches until fragrant; cool fully; store in a jar.",
           "Portion ~25 g per person at serving time."],
    storage={"fridge_days": None, "freezer_days": None,
             "note": "Airtight jar, keeps for weeks."},
    media={},
    tips=["Pre-portion so you don't overshoot calories."],
))


def main():
    os.makedirs(RECIPE_DIR, exist_ok=True)
    # registry
    with open(ING_FILE, "w") as f:
        yaml.safe_dump(build_registry(), f, sort_keys=False, allow_unicode=True,
                       default_flow_style=False)
    print(f"wrote {ING_FILE}")
    # recipes
    ids = set()
    for r in RECIPES:
        assert r["id"] not in ids, f"duplicate id {r['id']}"
        ids.add(r["id"])
        path = os.path.join(RECIPE_DIR, r["id"] + ".yaml")
        with open(path, "w") as f:
            yaml.safe_dump(r, f, sort_keys=False, allow_unicode=True,
                           default_flow_style=False)
    print(f"wrote {len(RECIPES)} recipe files to {RECIPE_DIR}")


if __name__ == "__main__":
    main()
