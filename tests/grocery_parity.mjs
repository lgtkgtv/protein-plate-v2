/* Parity test: the shared JS grocery core must produce the same normalized
 * amounts as the Python aggregator. Run after tests/gen_parity.py has written
 * the fixture:
 *     uv run python tests/gen_parity.py && node tests/grocery_parity.mjs
 */
import fs from "node:fs";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const core = require("../docs/assets/js/grocery-core.js");

const fixture = JSON.parse(fs.readFileSync("/tmp/pp_parity.json", "utf8"));
const { payload, cases } = fixture;

function actualFor(counts) {
  const grouped = core.aggregate(counts, payload);
  const out = {};
  grouped.forEach((cat) => {
    cat.items.forEach((it) => {
      if (it.parts && it.parts.length) {
        out[cat.cat + "||" + it.display] =
          it.parts.map((p) => [Math.round(p[0] * 1000) / 1000, p[1]]);
      }
    });
  });
  return out;
}

let failures = 0;
for (const c of cases) {
  const actual = actualFor(c.counts);
  const expected = c.expected;
  const keys = new Set([...Object.keys(expected), ...Object.keys(actual)]);
  for (const k of keys) {
    const a = JSON.stringify(actual[k]);
    const e = JSON.stringify(expected[k]);
    if (a !== e) {
      failures++;
      console.log(`MISMATCH [${c.name}] ${k}\n  python: ${e}\n  js:     ${a}`);
    }
  }
}

if (failures) {
  console.log(`\n${failures} mismatch(es)`);
  process.exit(1);
}
console.log(`parity OK: ${cases.length} cases, JS matches Python`);
