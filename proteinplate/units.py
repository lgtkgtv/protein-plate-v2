"""Unit normalization for the grocery list.

The aggregator can collect the same ingredient in several units (oil as both
tbsp and tsp, besan as cup + tbsp + tsp). This module groups those quantities by
physical dimension and sums the convertible ones, so each ingredient shows as
one tidy amount instead of three.

Rules, kept deliberately simple:
  - Volume units (ml, l, tsp, tbsp, cup) convert to a base of millilitres using
    culinary-standard rounded factors, then render in the largest unit that
    yields a number >= 1 (l -> cup -> tbsp -> tsp).
  - Mass units (g, kg) convert to grams, render as kg above 1000 g else g.
  - Count / fuzzy units (piece, clove, sprig, bunch, handful, head, pinch) are
    NOT interconvertible; they're summed within their own unit and kept as-is.
  - If one ingredient appears in two different dimensions (e.g. lemon as whole
    pieces AND as tbsp of juice), both are kept — converting between them would
    need yield data we don't model.
"""

# Base units: volume -> millilitres, mass -> grams. Culinary-standard rounding.
_VOLUME_ML = {"ml": 1.0, "l": 1000.0, "tsp": 5.0, "tbsp": 15.0, "cup": 240.0}
_MASS_G = {"g": 1.0, "kg": 1000.0}

# Count / fuzzy units that are summed but never converted.
_COUNT_UNITS = {"piece", "clove", "sprig", "bunch", "handful", "head", "pinch"}


def dimension(unit):
    if unit in _VOLUME_ML:
        return "volume"
    if unit in _MASS_G:
        return "mass"
    if unit in _COUNT_UNITS:
        return "count"
    return None  # to_taste / as_needed / unknown -> caller handles separately


import math


def _round_to(x, step):
    # Half-up rounding (not Python's banker's rounding), so a small spice amount
    # never collapses to "0 tsp" and the result matches the browser's Math.round.
    return math.floor(x / step + 0.5) * step


def _render_volume(ml):
    # Cups are the largest everyday unit for both dry (besan, chickpeas) and wet
    # (curd, oil) goods; only roll up to litres for genuinely large volumes.
    if ml >= 2000:
        return (_round_to(ml / 1000.0, 0.1), "l")
    if ml >= 180:                       # ~3/4 cup and up
        return (_round_to(ml / 240.0, 0.25), "cup")
    if ml >= 15:
        return (_round_to(ml / 15.0, 0.5), "tbsp")
    return (_round_to(ml / 5.0, 0.5), "tsp")


def _render_mass(g):
    if g >= 1000:
        return (_round_to(g / 1000.0, 0.1), "kg")
    return (_round_to(g, 5), "g")


def to_base(qty, unit):
    """Convert one (qty, unit) to a canonical (dim, value).

    dim is "mass" (grams), "volume" (millilitres), "count:<unit>" (kept as-is),
    or "taste" (value None). This is the single source for conversion factors;
    the web export reuses it so the browser never re-implements them.
    """
    d = dimension(unit)
    if d == "volume":
        return ("volume", qty * _VOLUME_ML[unit])
    if d == "mass":
        return ("mass", qty * _MASS_G[unit])
    if d == "count":
        return ("count:" + unit, qty)
    return ("count:" + unit, qty)  # forgiving for unknown units


def render_base(dim, value):
    """Render a summed canonical value back to a display (qty, unit)."""
    if dim == "mass":
        return _render_mass(value)
    if dim == "volume":
        return _render_volume(value)
    return (value, dim.split(":", 1)[1])  # count:<unit>


def normalize(amounts):
    """amounts: iterable of (qty, unit) with numeric qty.

    Returns a list of (qty, unit) display amounts, minimal per dimension and
    ordered mass -> volume -> count for stable, readable output.
    """
    mass_g = vol_ml = 0.0
    have_mass = have_vol = False
    counts = {}  # "count:<unit>" -> qty

    for qty, unit in amounts:
        dim, value = to_base(qty, unit)
        if dim == "mass":
            mass_g += value
            have_mass = True
        elif dim == "volume":
            vol_ml += value
            have_vol = True
        else:
            counts[dim] = counts.get(dim, 0.0) + value

    out = []
    if have_mass:
        out.append(render_base("mass", mass_g))
    if have_vol:
        out.append(render_base("volume", vol_ml))
    for dim, qty in sorted(counts.items()):
        out.append(render_base(dim, qty))
    return out
