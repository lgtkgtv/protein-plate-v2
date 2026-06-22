/* Dynamic grocery list.
 *
 * Reads the embedded recipe data (#pp-data) and the saved plan ("pp-plan"),
 * lets you scope to the whole plan / a single day / a single meal, and renders
 * the list with the shared core (grocery-core.js, parity-tested against Python).
 * Checkboxes persist per scope; a toolbar shows basket progress. Falls back to
 * the server-rendered week list if anything is missing.
 */
(function () {
  "use strict";
  var PLAN_KEY = "pp-plan";

  function readData() {
    var el = document.getElementById("pp-data");
    if (!el) return null;
    try { return JSON.parse(el.textContent); } catch (e) { return null; }
  }
  function effectivePlan(data) {
    var saved = {};
    try { saved = JSON.parse(localStorage.getItem(PLAN_KEY)) || {}; } catch (e) {}
    return data.defaultPlan.map(function (d) {
      var s = saved[d.day] || {};
      return {
        day: d.day,
        protein: s.protein || d.protein,
        cooked_veg: s.cooked_veg || d.cooked_veg,
        salad: s.salad || d.salad,
        extras: d.extras || []
      };
    });
  }

  function checkKey(scope, label) {
    return "pp-check:" + location.pathname + "|" + scope + "|" + label;
  }
  function getChecked(k) { try { return localStorage.getItem(k) === "1"; } catch (e) { return false; } }
  function setChecked(k, on) {
    try { on ? localStorage.setItem(k, "1") : localStorage.removeItem(k); } catch (e) {}
  }

  function init() {
    var app = document.getElementById("pp-grocery-app");
    var data = readData();
    if (!app || !data || !window.PPGrocery) return;       // keep the fallback

    var fallback = document.getElementById("pp-grocery-fallback");
    if (fallback) fallback.hidden = true;

    var plan = effectivePlan(data);

    // Build the scope selector: whole plan, each day, each single meal.
    var select = document.createElement("select");
    select.id = "pp-scope-select";
    select.className = "pp-scope__select";
    select.appendChild(opt("all", "My whole plan"));
    var gDays = group("A single day");
    plan.forEach(function (d) { gDays.appendChild(opt(d.day, d.day)); });
    select.appendChild(gDays);
    var gMeals = group("A single meal");
    Object.keys(data.recipes)
      .sort(function (a, b) { return data.recipes[a].name < data.recipes[b].name ? -1 : 1; })
      .forEach(function (rid) { gMeals.appendChild(opt("meal:" + rid, data.recipes[rid].name)); });
    select.appendChild(gMeals);

    var bar = document.createElement("div");
    bar.className = "pp-scope";
    var lbl = document.createElement("label");
    lbl.setAttribute("for", "pp-scope-select");
    lbl.textContent = "Shopping for";
    bar.appendChild(lbl);
    bar.appendChild(select);

    var cart = document.createElement("div");
    cart.className = "pp-cart";
    var count = document.createElement("span");
    count.className = "pp-cart__count";
    var reset = document.createElement("button");
    reset.type = "button";
    reset.className = "pp-cart__reset";
    reset.textContent = "Reset";
    cart.appendChild(count);
    cart.appendChild(reset);

    var listEl = document.createElement("div");
    listEl.className = "pp-scope-list";

    app.innerHTML = "";
    app.appendChild(bar);
    app.appendChild(cart);
    app.appendChild(listEl);

    var boxes = [];

    function refresh() {
      var done = boxes.filter(function (b) { return b.input.checked; }).length;
      count.textContent = done + " / " + boxes.length + " in the basket";
    }

    function render(scope) {
      var counts = window.PPGrocery.planCounts(plan, data, scope);
      var groups = window.PPGrocery.aggregate(counts, data);
      listEl.innerHTML = "";
      boxes = [];
      if (!groups.length) {
        listEl.innerHTML = "<p>Nothing to shop for in this selection.</p>";
        refresh();
        return;
      }
      groups.forEach(function (g) {
        var h = document.createElement("p");
        h.className = "pp-cat";
        h.innerHTML = "<strong>" + g.heading + "</strong>";
        listEl.appendChild(h);
        var ul = document.createElement("ul");
        ul.className = "task-list";
        g.items.forEach(function (it) {
          var li = document.createElement("li");
          li.className = "task-list-item";
          var label = document.createElement("label");
          var input = document.createElement("input");
          input.type = "checkbox";
          input.className = "task-list-control";
          var k = checkKey(scope, it.display);
          if (getChecked(k)) { input.checked = true; li.classList.add("pp-checked"); }
          input.addEventListener("change", function () {
            setChecked(k, input.checked);
            li.classList.toggle("pp-checked", input.checked);
            refresh();
          });
          var note = it.note ? '  <em>(' + it.note + ")</em>" : "";
          label.appendChild(input);
          label.insertAdjacentHTML("beforeend",
            " " + it.display + " \u2014 " + it.amount + note);
          li.appendChild(label);
          ul.appendChild(li);
          boxes.push({ input: input });
        });
        listEl.appendChild(ul);
      });
      refresh();
    }

    select.addEventListener("change", function () { render(select.value); });
    reset.addEventListener("click", function () {
      boxes.forEach(function (b) { b.input.checked = false; });
      var scope = select.value;
      // clear stored ticks for the visible items
      Array.prototype.slice.call(listEl.querySelectorAll(".task-list-item"))
        .forEach(function (li) {
          var txt = (li.textContent || "").trim();
          var dash = txt.indexOf("\u2014");
          var name = (dash > 0 ? txt.slice(0, dash) : txt).trim();
          setChecked(checkKey(scope, name), false);
          li.classList.remove("pp-checked");
        });
      refresh();
    });

    render("all");

    function opt(v, t) { var o = document.createElement("option"); o.value = v; o.textContent = t; return o; }
    function group(t) { var g = document.createElement("optgroup"); g.label = t; return g; }
  }

  if (window.document$ && typeof window.document$.subscribe === "function") {
    window.document$.subscribe(init);
  } else {
    document.addEventListener("DOMContentLoaded", init);
  }
})();
