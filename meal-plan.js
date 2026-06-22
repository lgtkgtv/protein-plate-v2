/* Meal-plan duration filter.
 *
 * Shows the first 1, 3, or 7 days of the plan table. The "cook once" batches
 * table below is week-level and is left untouched.
 */
(function () {
  "use strict";

  function init() {
    var ctrl = document.querySelector(".pp-duration");
    if (!ctrl) return;
    var table = document.querySelector(".md-typeset table");  // first = day plan
    if (!table) return;
    var rows = Array.prototype.slice.call(table.querySelectorAll("tbody tr"));

    function apply(n) {
      rows.forEach(function (row, i) {
        // inline style beats theme table CSS that the [hidden] attribute can't
        row.style.display = i < n ? "" : "none";
      });
    }

    ctrl.addEventListener("click", function (e) {
      var btn = e.target.closest("button[data-days]");
      if (!btn) return;
      ctrl.querySelectorAll("button").forEach(function (b) {
        b.setAttribute("aria-pressed", b === btn ? "true" : "false");
      });
      apply(parseInt(btn.dataset.days, 10));
    });
    // default: full week (all rows visible)
  }

  if (window.document$ && typeof window.document$.subscribe === "function") {
    window.document$.subscribe(init);
  } else {
    document.addEventListener("DOMContentLoaded", init);
  }
})();
