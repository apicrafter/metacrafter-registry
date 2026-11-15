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

  var escapeHtml = function (text) {
    var div = document.createElement("div");
    div.textContent = text == null ? "" : String(text);
    return div.innerHTML;
  };

  // Column headers become sort buttons; a second click reverses the order.
  // onSort(column, descending) does the sorting.
  var makeSortable = function (table, onSort) {
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
        onSort(column, descending);
        headers.forEach(function (other) { other.removeAttribute("aria-sort"); });
        th.setAttribute("aria-sort", descending ? "descending" : "ascending");
      });
    });
  };

  // Empty keys go last in both directions.
  var compareKeys = function (a, b, descending) {
    if (!a || !b) return a ? -1 : b ? 1 : 0;
    var order = a.localeCompare(b, undefined, { numeric: true });
    return descending ? -order : order;
  };

  // Sortable tables: <table data-sortable> sorts its own rows.
  document.querySelectorAll("table[data-sortable]").forEach(function (table) {
    var body = table.tBodies[0];
    makeSortable(table, function (column, descending) {
      var rows = Array.prototype.slice.call(body.rows).map(function (row) {
        return { row: row, key: norm(row.cells[column].textContent).trim() };
      });
      rows.sort(function (a, b) { return compareKeys(a.key, b.key, descending); });
      var fragment = document.createDocumentFragment();
      rows.forEach(function (item) { fragment.appendChild(item.row); });
      body.appendChild(fragment);
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

  // Datatype list. The page has the first records as HTML rows; the compact
  // index brings all of them. Until it arrives the filters work on the HTML
  // rows; after that the table is rendered from the index, one page at a time.
  var filterForm = document.getElementById("filters");
  if (filterForm) {
    var FIELDS = ["q", "category", "country", "kind", "status", "rules", "pii"];
    var PAGE_SIZE = 100;
    var listTable = document.getElementById("datatype-table");
    var listBody = listTable.tBodies[0];
    var counter = document.getElementById("result-count");
    var pager = document.getElementById("pager");
    var pagerStatus = document.getElementById("pager-status");
    var words = function (value) { return (value || "").split(" ").filter(Boolean); };
    var htmlRows = Array.prototype.slice.call(listBody.rows);
    var htmlEntries = htmlRows.map(function (row) {
      return {
        text: row.getAttribute("data-text"),
        categories: words(row.getAttribute("data-categories")),
        country: words(row.getAttribute("data-country")).filter(function (c) { return c !== "any"; }),
        kind: row.getAttribute("data-kind"),
        status: row.getAttribute("data-status"),
        has_rules: row.getAttribute("data-rules") === "yes",
        is_pii: row.getAttribute("data-pii") === "yes"
      };
    });
    var entries = null, loadFailed = false, loadedBytes = 0;
    var page = 0, sortColumn = -1, sortDescending = false;
    var SORT_KEYS = [
      function (e) { return e.id; },
      function (e) { return norm(e.name); },
      function (e) { return e.categories.join(" "); },
      function (e) { return e.country.join(" "); },
      function (e) { return norm(e.doc); }
    ];

    var listParams = new URLSearchParams(window.location.search);
    FIELDS.forEach(function (name) {
      var field = filterForm.elements[name];
      if (field && listParams.get(name)) field.value = listParams.get(name);
    });
    page = Math.max(0, (parseInt(listParams.get("page"), 10) || 1) - 1);

    var matches = function (e, f) {
      return (!f.q || e.text.indexOf(f.q) !== -1) &&
        (!f.category || e.categories.indexOf(f.category) !== -1) &&
        (!f.country || (f.country === "any" ? !e.country.length : e.country.indexOf(f.country) !== -1)) &&
        (!f.kind || e.kind === f.kind) &&
        (!f.status || e.status === f.status) &&
        (!f.rules || e.has_rules === (f.rules === "yes")) &&
        (!f.pii || e.is_pii === (f.pii === "yes"));
    };

    var links = function (ids, folder) {
      return ids.map(function (id) {
        return '<a href="' + base + "/" + folder + "/" + encodeURIComponent(id) + '">' + escapeHtml(id) + "</a>";
      }).join(", ");
    };

    var rowHtml = function (e) {
      var href = base + "/datatype/" + encodeURIComponent(e.id);
      return '<tr><td class="id"><a href="' + href + '">' + escapeHtml(e.id) + "</a></td>" +
        '<td><a href="' + href + '">' + escapeHtml(e.name) + "</a>" +
        (e.is_pii ? ' <span class="badge pii">PII</span>' : "") +
        (e.kind === "pattern" ? ' <span class="badge neutral">pattern</span>' : "") +
        (e.status === "stable" ? ' <span class="badge ok" title="Reviewed">stable</span>' : "") +
        (e.status === "deprecated" ? ' <span class="badge neutral">deprecated</span>' : "") + "</td>" +
        "<td>" + links(e.categories, "category") + "</td>" +
        "<td>" + (e.country.length ? links(e.country, "country") : '<span class="muted">global</span>') + "</td>" +
        '<td class="doc">' + escapeHtml(e.doc) + "</td></tr>";
    };

    var apply = function () {
      var f = {};
      FIELDS.forEach(function (name) { f[name] = filterForm.elements[name].value; });
      f.q = norm(f.q).trim();
      if (!entries) {
        var shown = 0;
        htmlEntries.forEach(function (e, i) {
          var ok = matches(e, f);
          htmlRows[i].hidden = !ok;
          if (ok) shown += 1;
        });
        // The rows on the page are only the first ones: say so, or an empty
        // table would read as "no such records".
        counter.textContent = loadFailed
          ? "Could not load the full list. " + shown + " of the first " + htmlRows.length + " records match."
          : "Loading all records… " + (loadedBytes / 1048576).toFixed(1) + " MB. " +
            shown + " of the first " + htmlRows.length + " match so far.";
      } else {
        var hits = entries.filter(function (e) { return matches(e, f); });
        if (sortColumn >= 0) {
          var key = SORT_KEYS[sortColumn];
          hits.sort(function (a, b) { return compareKeys(key(a), key(b), sortDescending); });
        }
        var pages = Math.max(1, Math.ceil(hits.length / PAGE_SIZE));
        page = Math.min(page, pages - 1);
        var first = page * PAGE_SIZE;
        var slice = hits.slice(first, first + PAGE_SIZE);
        listBody.innerHTML = slice.map(rowHtml).join("");
        counter.textContent = hits.length
          ? "Showing " + (first + 1) + "–" + (first + slice.length) + " of " + hits.length +
            (hits.length < entries.length ? " (filtered from " + entries.length + ")" : "")
          : "No records match these filters.";
        pager.hidden = pages < 2;
        pagerStatus.textContent = "Page " + (page + 1) + " of " + pages;
        pager.querySelector('[data-step="-1"]').disabled = page === 0;
        pager.querySelector('[data-step="1"]').disabled = page >= pages - 1;
      }
      var state = new URLSearchParams();
      FIELDS.forEach(function (name) {
        var value = filterForm.elements[name].value;
        if (value) state.set(name, value);
      });
      if (page > 0) state.set("page", String(page + 1));
      var query = state.toString();
      history.replaceState(null, "", window.location.pathname + (query ? "?" + query : ""));
    };

    var requestedPage = page;
    filterForm.addEventListener("input", function () { page = 0; requestedPage = 0; apply(); });
    filterForm.addEventListener("submit", function (event) { event.preventDefault(); apply(); });
    pager.addEventListener("click", function (event) {
      var step = parseInt(event.target.getAttribute("data-step"), 10);
      if (!step) return;
      page += step;
      apply();
      listTable.scrollIntoView();
    });
    filterForm.hidden = false;
    apply();

    window.registryFetchJson(base + "/api/v1/datatypes-index.json", function (bytes) {
      loadedBytes = bytes;
      if (!entries) apply();
    })
      .then(function (data) {
        data.forEach(function (e) {
          e.text = norm([e.id, e.name].concat(e.names || [], [e.doc]).join(" "));
        });
        entries = data;
        page = requestedPage;
        makeSortable(listTable, function (column, descending) {
          sortColumn = column;
          sortDescending = descending;
          page = 0;
          apply();
        });
        apply();
      })
      .catch(function () { loadFailed = true; apply(); });
  }

  // Search page: ranks records from the compact index; nothing leaves the browser.
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
        if (entry.nameText.indexOf(t) !== -1) s = Math.max(s, 35);
        if (entry.namesText.indexOf(t) !== -1) s = Math.max(s, 25);
        if (entry.groupText.indexOf(t) !== -1) s = Math.max(s, 10);
        if (entry.docText.indexOf(t) !== -1) s = Math.max(s, 8);
        if (!s) return 0;
        total += s;
      }
      return total;
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
          '<a href="' + base + "/datatype/" + encodeURIComponent(e.id) + '"><strong>' + escapeHtml(e.name) + "</strong></a> " +
          '<code>' + escapeHtml(e.id) + "</code>" +
          (e.is_pii ? ' <span class="badge pii">PII</span>' : "") +
          (e.kind === "pattern" ? ' <span class="badge neutral">pattern</span>' : "") +
          (e.status === "stable" ? ' <span class="badge ok">stable</span>' : "") +
          '<div class="meta">' + escapeHtml(e.doc) + "</div>";
        results.appendChild(li);
      });
    };

    var params = new URLSearchParams(window.location.search);
    input.value = params.get("q") || "";
    status.textContent = "Loading index…";
    window.registryFetchJson(base + "/api/v1/datatypes-index.json", function (bytes) {
      status.textContent = "Loading index… " + (bytes / 1048576).toFixed(1) + " MB";
    })
      .then(function (data) {
        data.forEach(function (e) {
          e.nameText = norm(e.name);
          e.namesText = norm((e.names || []).join(" "));
          e.groupText = norm(e.categories.concat(e.country).join(" "));
          e.docText = norm(e.doc);
        });
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
