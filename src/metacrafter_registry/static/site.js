// Metacrafter Registry — progressive enhancement only; every page works without it.
(function () {
  "use strict";

  var base = document.documentElement.getAttribute("data-base") || "";

  function norm(value) {
    return (value || "").toString().toLowerCase();
  }

  // Copy-to-clipboard buttons: <button data-copy="text">
  document.querySelectorAll("[data-copy]").forEach(function (button) {
    button.hidden = false;
    button.addEventListener("click", function () {
      var text = button.getAttribute("data-copy");
      if (!navigator.clipboard) return;
      navigator.clipboard.writeText(text).then(function () {
        var label = button.textContent;
        button.textContent = "Copied";
        setTimeout(function () { button.textContent = label; }, 1200);
      });
    });
  });

  // Datatype list filters: rows carry data-* attributes, the form drives them.
  var filterForm = document.getElementById("filters");
  if (filterForm) {
    var rows = Array.prototype.slice.call(document.querySelectorAll("#datatype-table tbody tr"));
    var counter = document.getElementById("result-count");
    var params = new URLSearchParams(window.location.search);
    ["q", "category", "country", "kind", "status", "rules", "pii"].forEach(function (name) {
      var field = filterForm.elements[name];
      if (field && params.get(name)) field.value = params.get(name);
    });

    var apply = function () {
      var q = norm(filterForm.elements.q.value).trim();
      var category = filterForm.elements.category.value;
      var country = filterForm.elements.country.value;
      var kind = filterForm.elements.kind.value;
      var pii = filterForm.elements.pii.value;
      var status = filterForm.elements.status.value;
      var rulesFilter = filterForm.elements.rules.value;
      var shown = 0;
      rows.forEach(function (row) {
        var ok =
          (!q || row.getAttribute("data-text").indexOf(q) !== -1) &&
          (!category || (" " + row.getAttribute("data-categories") + " ").indexOf(" " + category + " ") !== -1) &&
          (!country || (" " + row.getAttribute("data-country") + " ").indexOf(" " + country + " ") !== -1) &&
          (!kind || row.getAttribute("data-kind") === kind) &&
          (!status || row.getAttribute("data-status") === status) &&
          (!rulesFilter || row.getAttribute("data-rules") === rulesFilter) &&
          (!pii || row.getAttribute("data-pii") === pii);
        row.hidden = !ok;
        if (ok) shown += 1;
      });
      counter.textContent = "Showing " + shown + " of " + rows.length;
      var state = new URLSearchParams();
      ["q", "category", "country", "kind", "status", "rules", "pii"].forEach(function (name) {
        var value = filterForm.elements[name].value;
        if (value) state.set(name, value);
      });
      var query = state.toString();
      history.replaceState(null, "", window.location.pathname + (query ? "?" + query : ""));
    };
    filterForm.addEventListener("input", apply);
    filterForm.addEventListener("submit", function (event) { event.preventDefault(); apply(); });
    filterForm.hidden = false;
    apply();
  }

  // Search page: ranks records from search-index.json; nothing leaves the browser.
  var results = document.getElementById("search-results");
  if (results) {
    var input = document.getElementById("search-q");
    var status = document.getElementById("search-status");
    var index = null;

    var score = function (entry, tokens) {
      var total = 0;
      for (var i = 0; i < tokens.length; i += 1) {
        var t = tokens[i];
        var s = 0;
        if (entry.id === t) s = 100;
        else if (entry.id.indexOf(t) === 0) s = 60;
        else if (entry.id.indexOf(t) !== -1) s = 40;
        if (norm(entry.n).indexOf(t) !== -1) s = Math.max(s, 35);
        if (norm(entry.t).indexOf(t) !== -1) s = Math.max(s, 25);
        if (norm(entry.c).indexOf(t) !== -1) s = Math.max(s, 10);
        if (norm(entry.d).indexOf(t) !== -1) s = Math.max(s, 8);
        if (!s) return 0;
        total += s;
      }
      return total;
    };

    var escapeHtml = function (text) {
      var div = document.createElement("div");
      div.textContent = text || "";
      return div.innerHTML;
    };

    var render = function () {
      var q = norm(input.value).trim();
      var tokens = q.split(/\s+/).filter(Boolean);
      results.innerHTML = "";
      if (!tokens.length) { status.textContent = "Type to search " + index.length + " datatypes and patterns."; return; }
      var hits = index
        .map(function (entry) { return { entry: entry, s: score(entry, tokens) }; })
        .filter(function (hit) { return hit.s > 0; })
        .sort(function (a, b) { return b.s - a.s || a.entry.id.localeCompare(b.entry.id); });
      status.textContent = hits.length + " result" + (hits.length === 1 ? "" : "s") + " for “" + input.value.trim() + "”";
      hits.slice(0, 100).forEach(function (hit) {
        var e = hit.entry;
        var li = document.createElement("li");
        li.innerHTML =
          '<a href="' + base + "/datatype/" + encodeURIComponent(e.id) + '"><strong>' + escapeHtml(e.n) + "</strong></a> " +
          '<code>' + escapeHtml(e.id) + "</code>" +
          (e.p ? ' <span class="badge pii">PII</span>' : "") +
          (e.k === "pattern" ? ' <span class="badge neutral">pattern</span>' : "") +
          (e.s === "draft" ? ' <span class="badge draft">draft</span>' : "") +
          '<div class="meta">' + escapeHtml(e.d) + "</div>";
        results.appendChild(li);
      });
    };

    var params = new URLSearchParams(window.location.search);
    input.value = params.get("q") || "";
    status.textContent = "Loading index…";
    fetch(base + "/search-index.json")
      .then(function (response) { return response.json(); })
      .then(function (data) {
        index = data;
        render();
        input.addEventListener("input", function () {
          var query = input.value.trim();
          history.replaceState(null, "", window.location.pathname + (query ? "?q=" + encodeURIComponent(query) : ""));
          render();
        });
      })
      .catch(function () { status.textContent = "Could not load the search index."; });
  }
})();
