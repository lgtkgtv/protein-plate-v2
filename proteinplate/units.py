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


def _round_to(x, step):
    return round(x / step) * step


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


def normalize(amounts):
    """amounts: iterable of (qty, unit) with numeric qty.

    Returns a list of (qty, unit) display amounts, minimal per dimension and
    ordered mass -> volume -> count for stable, readable output.
    """
    vol_ml = mass_g = 0.0
    have_vol = have_mass = False
    counts = {}  # unit -> qty

    for qty, unit in amounts:
        dim = dimension(unit)
        if dim == "volume":
            vol_ml += qty * _VOLUME_ML[unit]
            have_vol = True
        elif dim == "mass":
            mass_g += qty * _MASS_G[unit]
            have_mass = True
        elif dim == "count":
            counts[unit] = counts.get(unit, 0.0) + qty
        else:
            counts[unit] = counts.get(unit, 0.0) + qty  # be forgiving

    out = []
    if have_mass:
        out.append(_render_mass(mass_g))
    if have_vol:
        out.append(_render_volume(vol_ml))
    for unit, qty in sorted(counts.items()):
        out.append((qty, unit))
    return out
