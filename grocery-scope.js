/* Grocery list: scope switching + persistent checkboxes + basket toolbar.
 *
 * The page ships one pre-rendered list per scope (whole week, each day, each
 * 3-day window, each single meal), all generated in Python so the amounts can
 * never disagree with the recipes. This script just shows the chosen one, keeps
 * ticks in localStorage (per scope, so each list is its own checklist), and
 * shows a "N / M in the basket" toolbar for the visible list. Replaces the
 * earlier grocery-checklist.js.
 */
(function () {
  "use strict";

  function keyFor(path, scope, label) {
    return "pp-check:" + path + "|" + scope + "|" + label;
  }
  function labelOf(li) {
    var t = (li.textContent || "").trim();
    var dash = t.indexOf("\u2014"); // em dash separates name from quantity
    return (dash > 0 ? t.slice(0, dash) : t).trim();
  }
  function get(k) { try { return localStorage.getItem(k) === "1"; } catch (e) { return false; } }
  function set(k, on) {
    try { on ? localStorage.setItem(k, "1") : localStorage.removeItem(k); } catch (e) {}
  }

  function init() {
    var lists = Array.prototype.slice.call(
      document.querySelectorAll(".pp-scope-list"));
    if (!lists.length) return;

    var path = location.pathname;
    var select = document.getElementById("pp-scope-select");

    var toolbar = document.createElement("div");
    toolbar.className = "pp-cart";
    var count = document.createElement("span");
    count.className = "pp-cart__count";
    var reset = document.createElement("button");
    reset.type = "button";
    reset.className = "pp-cart__reset";
    reset.textContent = "Reset";
    toolbar.appendChild(count);
    toolbar.appendChild(reset);
    lists[0].parentNode.insertBefore(toolbar, lists[0]);

    function visible() {
      for (var i = 0; i < lists.length; i++) {
        if (!lists[i].hidden) return lists[i];
      }
      return lists[0];
    }
    function boxesIn(list) {
      return Array.prototype.slice.call(
        list.querySelectorAll(".task-list-item input[type=checkbox]"));
    }
    function refresh() {
      var boxes = boxesIn(visible());
      var done = boxes.filter(function (b) { return b.checked; }).length;
      count.textContent = done + " / " + boxes.length + " in the basket";
    }
    function bind(list) {
      if (list.dataset.ppBound) return;
      list.dataset.ppBound = "1";
      var scope = list.dataset.scope;
      boxesIn(list).forEach(function (box) {
        box.disabled = false;
        var li = box.closest("li");
        var k = keyFor(path, scope, labelOf(li));
        if (get(k)) box.checked = true;
        li.classList.toggle("pp-checked", box.checked);
        box.addEventListener("change", function () {
          set(k, box.checked);
          li.classList.toggle("pp-checked", box.checked);
          refresh();
        });
      });
    }

    bind(visible());
    refresh();

    if (select) {
      select.addEventListener("change", function () {
        var scope = select.value;
        lists.forEach(function (l) { l.hidden = l.dataset.scope !== scope; });
        bind(visible());
        refresh();
      });
    }

    reset.addEventListener("click", function () {
      var list = visible();
      boxesIn(list).forEach(function (box) {
        box.checked = false;
        var li = box.closest("li");
        set(keyFor(path, list.dataset.scope, labelOf(li)), false);
        li.classList.remove("pp-checked");
      });
      refresh();
    });
  }

  if (window.document$ && typeof window.document$.subscribe === "function") {
    window.document$.subscribe(init);
  } else {
    document.addEventListener("DOMContentLoaded", init);
  }
})();
