"""Write a fixture the Node parity test consumes: the web payload plus, for a
set of recipe-count maps, the expected normalized amounts straight from the
Python aggregator. If the JS core drifts from units.py/grocery.py, the Node test
that reads this file fails.
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from proteinplate import data, grocery, webdata  # noqa: E402


def expected_for(counts):
    totals, _to_taste, _notes = grocery.aggregate(counts)
    out = {}
    for t in totals:
        key = t["category"] + "||" + t["display"]
        out[key] = [[round(q, 3), u] for q, u in t["amounts"]]
    return out


def main():
    mp = data.meal_plan()
    day0 = mp["days"][0]
    day_counts = {}
    for slot in ("protein", "cooked_veg", "salad"):
        if day0.get(slot):
            day_counts[day0[slot]] = day_counts.get(day0[slot], 0) + 1
    for rid in day0.get("extras", []):
        day_counts[rid] = day_counts.get(rid, 0) + 1

    cases = [
        {"name": "week-batches", "counts": dict(mp["batches"])},
        {"name": "single-day-monday", "counts": day_counts},
        {"name": "mixed-multipliers",
         "counts": {"paneer-bhurji": 2, "chana-masala": 1, "hummus": 3,
                    "kachumber": 2, "toasted-nuts-seeds": 1}},
        {"name": "single-meal", "counts": {"chicken-tikka-tawa": 1}},
    ]
    for c in cases:
        c["expected"] = expected_for(c["counts"])

    out = {"payload": webdata.payload(), "cases": cases}
    path = pathlib.Path("/tmp/pp_parity.json")
    path.write_text(json.dumps(out, ensure_ascii=False))
    print("wrote", path, "with", len(cases), "cases")


if __name__ == "__main__":
    main()
