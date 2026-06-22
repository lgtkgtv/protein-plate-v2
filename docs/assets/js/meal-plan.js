/* Configurable meal plan.
 *
 * The per-day dropdowns are the plan. This script saves the chosen meals to
 * localStorage (key "pp-plan") so they persist and so the grocery list can read
 * them, restores them on load, resets to the defaults, and filters the table to
 * 1 / 3 / 7 days. The defaults are the values rendered by the server.
 */
(function () {
  "use strict";
  var KEY = "pp-plan";

  function load() {
    try { return JSON.parse(localStorage.getItem(KEY)) || {}; }
    catch (e) { return {}; }
  }
  function save(plan) {
    try { localStorage.setItem(KEY, JSON.stringify(plan)); } catch (e) {}
  }

  function init() {
    var picks = Array.prototype.slice.call(document.querySelectorAll(".pp-pick"));
    var duration = document.querySelector(".pp-duration");
    if (!picks.length && !duration) return;

    // Restore saved choices into the dropdowns.
    var plan = load();
    picks.forEach(function (sel) {
      var day = sel.dataset.day, slot = sel.dataset.slot;
      if (plan[day] && plan[day][slot]) sel.value = plan[day][slot];
      sel.addEventListener("change", function () {
        var p = load();
        p[day] = p[day] || {};
        p[day][slot] = sel.value;
        save(p);
      });
    });

    // Duration filter (1 / 3 / 7 days).
    var rows = Array.prototype.slice.call(
      document.querySelectorAll("tr[data-day-index]"));
    function applyDays(n) {
      rows.forEach(function (row, i) { row.style.display = i < n ? "" : "none"; });
    }
    if (duration) {
      duration.addEventListener("click", function (e) {
        var days = e.target.closest("button[data-days]");
        if (days) {
          duration.querySelectorAll("button[data-days]").forEach(function (b) {
            b.setAttribute("aria-pressed", b === days ? "true" : "false");
          });
          applyDays(parseInt(days.dataset.days, 10));
          return;
        }
        if (e.target.closest(".pp-plan-reset")) {
          picks.forEach(function (sel) { sel.value = sel.dataset.default; });
          try { localStorage.removeItem(KEY); } catch (er) {}
        }
      });
    }
  }

  if (window.document$ && typeof window.document$.subscribe === "function") {
    window.document$.subscribe(init);
  } else {
    document.addEventListener("DOMContentLoaded", init);
  }
})();
