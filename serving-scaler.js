/* Serving scaler for the Recipes page.
 *
 * Rescales every quantity marked with .pp-qty to the chosen number of people.
 * Each span carries its base quantity (data-qty), the recipe's base servings
 * (data-base) and whether it scales at all (data-scale: 1 = scales linearly,
 * 0 = fixed, e.g. spices/salt/oil). Selection is in-memory only; persistence
 * arrives with the localStorage work in the next phase.
 */
(function () {
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

  function apply(target) {
    document.querySelectorAll(".pp-qty").forEach(function (el) {
      var base = parseFloat(el.dataset.qty);
      var servings = parseFloat(el.dataset.base) || 4;
      var scales = el.dataset.scale !== "0";
      var value = scales ? base * (target / servings) : base;
      el.textContent = format(value);
    });
    document.querySelectorAll(".pp-srv").forEach(function (el) {
      el.textContent = String(target);
    });
  }

  function init() {
    var group = document.querySelector(".pp-servings");
    if (!group) return;
    group.addEventListener("click", function (e) {
      var btn = e.target.closest("button[data-servings]");
      if (!btn) return;
      group.querySelectorAll("button").forEach(function (b) {
        b.setAttribute("aria-pressed", b === btn ? "true" : "false");
      });
      apply(parseFloat(btn.dataset.servings));
    });
  }

  // Material's instant navigation swaps page content without a full reload, so
  // re-init on each navigation if the observable is available; else DOM ready.
  if (window.document$ && typeof window.document$.subscribe === "function") {
    window.document$.subscribe(init);
  } else {
    document.addEventListener("DOMContentLoaded", init);
  }
})();
