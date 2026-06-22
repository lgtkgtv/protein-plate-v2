"""Tests for proteinplate.units.normalize — run: uv run python tests/test_grocery_units.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from proteinplate import units


def approx(a, b, tol=1e-6):
    return abs(a - b) <= tol


def test_volume_merges_to_one_unit():
    # 1 tbsp (15ml) + 2 tsp (10ml) = 25 ml -> tbsp tier (>=15, <240)
    out = units.normalize([(1, "tbsp"), (2, "tsp")])
    assert len(out) == 1, out
    qty, unit = out[0]
    assert unit == "tbsp" and approx(qty, round(25 / 15 / 0.5) * 0.5), out


def test_volume_rolls_up_to_cup():
    # 2 cup + 2 tbsp = 510 ml -> cup tier
    out = units.normalize([(2, "cup"), (2, "tbsp")])
    assert len(out) == 1 and out[0][1] == "cup", out
    assert out[0][0] >= 2, out


def test_mass_rolls_up_to_kg():
    out = units.normalize([(900, "g"), (700, "g")])  # 1600 g
    assert out == [(1.6, "kg")], out


def test_count_units_stay_separate_from_volume():
    # lemon as pieces AND juice in tbsp -> two amounts, count + volume
    out = units.normalize([(0.5, "piece"), (2, "tbsp"), (1, "tbsp")])
    units_seen = {u for _, u in out}
    assert "piece" in units_seen and "tbsp" in units_seen, out
    # the two tbsp contributions merged into one
    assert sum(1 for _, u in out if u == "tbsp") == 1, out


def test_different_count_units_not_merged():
    out = units.normalize([(2, "clove"), (1, "piece")])
    assert sorted(u for _, u in out) == ["clove", "piece"], out


def test_small_volume_stays_tsp():
    out = units.normalize([(0.5, "tsp")])  # 2.5 ml -> tsp tier
    assert out == [(0.5, "tsp")], out


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"PASS {t.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL {t.__name__}: {e}")
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
