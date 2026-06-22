/* Persistent grocery checklist.
 *
 * Makes the grocery-list checkboxes survive a page refresh (you're in the store;
 * a reload shouldn't lose your progress). State is stored in localStorage keyed
 * by the page path + the ingredient name (the text before the "—"), so it's
 * stable even when quantities change. Adds a small progress + Reset toolbar.
 *
 * Runs only where task-list checkboxes exist (the Grocery List page).
 */
(function () {
  "use strict";

  function keyFor(path, label) {
    return "pp-check:" + path + "|" + label;
  }

  // The ingredient name = text before the em dash, ignoring the quantity/note.
  function labelOf(li) {
    var text = (li.textContent || "").trim();
    var dash = text.indexOf("\u2014"); // em dash
    return (dash > 0 ? text.slice(0, dash) : text).trim();
  }

  function get(k) {
    try { return localStorage.getItem(k) === "1"; } catch (e) { return false; }
  }
  function set(k, on) {
    try { on ? localStorage.setItem(k, "1") : localStorage.removeItem(k); }
    catch (e) {}
  }

  function init() {
    var boxes = Array.prototype.slice.call(
      document.querySelectorAll(".task-list-item input[type=checkbox]"));
    if (!boxes.length) return;

    var path = location.pathname;
    var items = boxes.map(function (box) {
      var li = box.closest("li");
      return { box: box, li: li, key: keyFor(path, labelOf(li)) };
    });

    var toolbar = buildToolbar();

    function refresh() {
      var done = items.filter(function (it) { return it.box.checked; }).length;
      toolbar.count.textContent = done + " / " + items.length + " in the basket";
    }

    items.forEach(function (it) {
      it.box.disabled = false;                 // belt-and-braces with the extension
      if (get(it.key)) it.box.checked = true;
      it.li.classList.toggle("pp-checked", it.box.checked);
      it.box.addEventListener("change", function () {
        set(it.key, it.box.checked);
        it.li.classList.toggle("pp-checked", it.box.checked);
        refresh();
      });
    });

    toolbar.reset.addEventListener("click", function () {
      items.forEach(function (it) {
        it.box.checked = false;
        set(it.key, false);
        it.li.classList.remove("pp-checked");
      });
      refresh();
    });

    refresh();
  }

  function buildToolbar() {
    var content = document.querySelector(".md-content") || document.body;
    var firstH2 = content.querySelector("h2");

    var bar = document.createElement("div");
    bar.className = "pp-cart";
    var count = document.createElement("span");
    count.className = "pp-cart__count";
    var reset = document.createElement("button");
    reset.type = "button";
    reset.className = "pp-cart__reset";
    reset.textContent = "Reset";
    bar.appendChild(count);
    bar.appendChild(reset);

    if (firstH2) firstH2.parentNode.insertBefore(bar, firstH2);
    else content.appendChild(bar);
    return { bar: bar, count: count, reset: reset };
  }

  if (window.document$ && typeof window.document$.subscribe === "function") {
    window.document$.subscribe(init);   // Material instant navigation
  } else {
    document.addEventListener("DOMContentLoaded", init);
  }
})();
