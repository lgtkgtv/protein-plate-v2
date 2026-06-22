/* Shared grocery aggregation — used by the browser (grocery.js) and by a Node
 * parity test that checks it against the Python aggregator. Pure functions, no
 * DOM. The unit rendering tiers mirror proteinplate/units.py, which remains the
 * canonical spec (its Python tests + the Node parity test guard against drift).
 */
(function (root, factory) {
  if (typeof module === "object" && module.exports) module.exports = factory();
  else root.PPGrocery = factory();
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  var FRACTIONS = [
    [0.25, "\u00BC"], [0.5, "\u00BD"], [0.75, "\u00BE"],
    [0.3333, "\u2153"], [0.6667, "\u2154"]
  ];

  function format(x) {
    if (!isFinite(x)) return "";
    var whole = Math.floor(x + 1e-9);
    var frac = x - whole;
    for (var i = 0; i < FRACTIONS.length; i++) {
      if (Math.abs(frac - FRACTIONS[i][0]) < 0.04) {
        return (whole ? whole : "") + FRACTIONS[i][1];
      }
    }
    if (frac < 0.04) return String(whole);
    return String(Math.round(x * 100) / 100);
  }

  function roundTo(x, step) { return Math.round(x / step) * step; }

  function renderMass(g) {
    if (g >= 1000) return [roundTo(g / 1000, 0.1), "kg"];
    return [roundTo(g, 5), "g"];
  }
  function renderVolume(ml) {
    if (ml >= 2000) return [roundTo(ml / 1000, 0.1), "l"];
    if (ml >= 180) return [roundTo(ml / 240, 0.25), "cup"];
    if (ml >= 15) return [roundTo(ml / 15, 0.5), "tbsp"];
    return [roundTo(ml / 5, 0.5), "tsp"];
  }

  // counts: { recipeId: multiplier }. Returns grouped categories with items.
  function aggregate(counts, dataObj) {
    var recipes = dataObj.recipes;
    var acc = {};
    Object.keys(counts).forEach(function (rid) {
      var c = counts[rid];
      var rec = recipes[rid];
      if (!rec || !c) return;
      rec.ings.forEach(function (ig) {
        var key = ig.c + "||" + ig.d;
        var a = acc[key] || (acc[key] = {
          cat: ig.c, display: ig.d, note: "",
          mass: 0, vol: 0, haveMass: false, haveVol: false,
          counts: {}, taste: false
        });
        if (ig.note) a.note = ig.note;
        if (ig.taste) { a.taste = true; return; }
        if (ig.dim === "mass") { a.mass += ig.b * c; a.haveMass = true; }
        else if (ig.dim === "volume") { a.vol += ig.b * c; a.haveVol = true; }
        else { a.counts[ig.dim] = (a.counts[ig.dim] || 0) + ig.b * c; }
      });
    });

    Object.keys(acc).forEach(function (key) {
      var a = acc[key];
      var parts = [];
      if (a.haveMass) parts.push(renderMass(a.mass));
      if (a.haveVol) parts.push(renderVolume(a.vol));
      Object.keys(a.counts).sort().forEach(function (dim) {
        parts.push([a.counts[dim], dim.split(":")[1]]);
      });
      a.parts = parts;  // raw [qty, unit] pairs (used by the parity test)
      a.amount = parts.length
        ? parts.map(function (p) { return format(p[0]) + " " + p[1]; }).join(" + ")
        : "to taste / as needed";
    });

    var byCat = {};
    Object.keys(acc).forEach(function (k) {
      (byCat[acc[k].cat] = byCat[acc[k].cat] || []).push(acc[k]);
    });
    var result = [];
    dataObj.categories.forEach(function (pair) {
      var cat = pair[0], heading = pair[1];
      var items = (byCat[cat] || []).sort(function (x, y) {
        return x.display < y.display ? -1 : x.display > y.display ? 1 : 0;
      });
      if (items.length) result.push({ cat: cat, heading: heading, items: items });
    });
    return result;
  }

  // Build a {recipe: count} map for a scope over a plan.
  // scope: "all" | a day name | "meal:<recipeId>".
  // Condiments and batch items count once (made ahead), mains count per day.
  function planCounts(plan, dataObj, scope) {
    var recipes = dataObj.recipes;
    if (scope && scope.indexOf("meal:") === 0) {
      var m = {}; m[scope.slice(5)] = 1; return m;
    }
    function dayIds(d) {
      return [d.protein, d.cooked_veg, d.salad]
        .concat(d.extras || []).filter(Boolean);
    }
    if (scope && scope !== "all") {                 // a single day
      var counts = {};
      plan.forEach(function (d) {
        if (d.day === scope) dayIds(d).forEach(function (rid) {
          counts[rid] = (counts[rid] || 0) + 1;
        });
      });
      return counts;
    }
    // whole plan
    var appears = {};
    plan.forEach(function (d) {
      dayIds(d).forEach(function (rid) { appears[rid] = (appears[rid] || 0) + 1; });
    });
    var out = {};
    Object.keys(appears).forEach(function (rid) {
      var rec = recipes[rid];
      var once = rec && (rec.batch || rec.category === "condiment");
      out[rid] = once ? 1 : appears[rid];
    });
    return out;
  }

  return { format: format, aggregate: aggregate, planCounts: planCounts };
});
