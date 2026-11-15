// Metacrafter Registry — progressive enhancement only; every page works without it.
(function () {
  "use strict";

  var base = document.documentElement.getAttribute("data-base") || "";

  function norm(value) {
    return (value || "").toString().toLowerCase();
  }

  // Narrow screens: the main menu collapses behind a button.
  var navToggle = document.querySelector(".nav-toggle");
  var nav = document.getElementById("site-nav");
  if (navToggle && nav) {
    document.querySelector(".site-header").classList.add("nav-collapsible");
    navToggle.addEventListener("click", function () {
      var open = nav.classList.toggle("open");
      navToggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
  }

  // Sortable tables: <table data-sortable>; a click on a column header sorts
  // by that column, a second click reverses the order.
  document.querySelectorAll("table[data-sortable]").forEach(function (table) {
    var body = table.tBodies[0];
    var headers = Array.prototype.slice.call(table.querySelectorAll("thead th"));
    headers.forEach(function (th, column) {
      var button = document.createElement("button");
      button.type = "button";
      button.className = "sort-btn";
      button.textContent = th.textContent;
      th.textContent = "";
      th.appendChild(button);
      button.addEventListener("click", function () {
        var descending = th.getAttribute("aria-sort") === "ascending";
        var rows = Array.prototype.slice.call(body.rows).map(function (row) {
          return { row: row, key: norm(row.cells[column].textContent).trim() };
        });
        rows.sort(function (a, b) {
          // Empty cells go last in both directions.
          if (!a.key || !b.key) return a.key ? -1 : b.key ? 1 : 0;
          var order = a.key.localeCompare(b.key, undefined, { numeric: true });
          return descending ? -order : order;
        });
        var fragment = document.createDocumentFragment();
        rows.forEach(function (item) { fragment.appendChild(item.row); });
        body.appendChild(fragment);
        headers.forEach(function (other) { other.removeAttribute("aria-sort"); });
        th.setAttribute("aria-sort", descending ? "descending" : "ascending");
      });
    });
  });

  // JSON download that reports the bytes received so far, so that a large
  // index on a slow connection does not look stuck.
  window.registryFetchJson = function (url, onProgress) {
    return fetch(url).then(function (response) {
      if (!response.ok) throw new Error("HTTP " + response.status);
      if (!response.body || !window.TextDecoder) return response.json();
      var reader = response.body.getReader();
      var decoder = new TextDecoder("utf-8");
      var text = "", received = 0;
      var pump = function () {
        return reader.read().then(function (chunk) {
          if (chunk.done) return JSON.parse(text + decoder.decode());
          received += chunk.value.length;
          text += decoder.decode(chunk.value, { stream: true });
          onProgress(received);
          return pump();
        });
      };
      return pump();
    });
  };

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
          (e.s === "stable" ? ' <span class="badge ok">stable</span>' : "") +
          '<div class="meta">' + escapeHtml(e.d) + "</div>";
        results.appendChild(li);
      });
    };

    var params = new URLSearchParams(window.location.search);
    input.value = params.get("q") || "";
    status.textContent = "Loading index…";
    window.registryFetchJson(base + "/search-index.json", function (bytes) {
      status.textContent = "Loading index… " + (bytes / 1048576).toFixed(1) + " MB";
    })
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
