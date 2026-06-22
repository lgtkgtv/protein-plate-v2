/* Register the service worker.
 *
 * Derives the site base from the <link rel="manifest"> href (rendered by the
 * template with the correct base_url), so registration works at "/" or under a
 * project subpath without hardcoding the repo name. The worker file sits at the
 * site root, giving it scope over the whole app.
 */
(function () {
  "use strict";
  if (!("serviceWorker" in navigator)) return;

  function base() {
    var link = document.querySelector('link[rel="manifest"]');
    if (link && link.href) return link.href.replace(/manifest\.json.*$/, "");
    return new URL(".", location.href).href;
  }

  window.addEventListener("load", function () {
    var root = base();
    navigator.serviceWorker.register(root + "sw.js", { scope: root })
      .catch(function (err) { console.warn("SW registration failed:", err); });
  });
})();
