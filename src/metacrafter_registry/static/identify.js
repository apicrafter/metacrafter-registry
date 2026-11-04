// /identify page. The only network request is the index download; pasted
// values stay in this browser tab.
/* global IdentifyCore */
(function () {
  "use strict";

  var MAX_VALUES = 200, MAX_LENGTH = 256, PATTERN_BUDGET_MS = 250;
  var base = document.documentElement.getAttribute("data-base") || "";
  var form = document.getElementById("identify-form");
  if (!form) return;
  var status = document.getElementById("identify-status");
  var output = document.getElementById("identify-results");
  var index = null;

  function escapeHtml(text) {
    var div = document.createElement("div");
    div.textContent = text == null ? "" : String(text);
    return div.innerHTML;
  }

  function pct(x) { return x == null ? "–" : Math.round(x * 100) + "%"; }

  function render(results, skipped) {
    if (!results.length) {
      output.innerHTML = '<p class="notice">No datatype matches these values. Try adding the column name, or <a href="' +
        base + '/search">search</a> by keyword.</p>';
    } else {
      var rows = results.map(function (r) {
        return "<tr><td>" + r.score + "</td>" +
          '<td><a href="' + base + "/datatype/" + encodeURIComponent(r.id) + '">' + escapeHtml(r.name) + "</a> <code>" +
          escapeHtml(r.id) + "</code>" + (r.is_pii ? ' <span class="badge pii">PII</span>' : "") +
          (r.status === "draft" ? ' <span class="badge draft">draft</span>' : "") + "</td>" +
          "<td>" + pct(r.regexp_hit_rate) + "</td>" +
          "<td>" + (r.checksum ? escapeHtml(r.checksum.algorithm) + " " + pct(r.checksum.pass_rate) : "–") + "</td>" +
          "<td>" + (r.field_name_similarity ? pct(r.field_name_similarity) : "–") + "</td></tr>";
      }).join("");
      output.innerHTML = '<div class="table-wrap"><table><thead><tr><th scope="col">Score</th><th scope="col">Datatype</th>' +
        '<th scope="col">Regexp hits</th><th scope="col">Check digit</th><th scope="col">Field name</th></tr></thead>' +
        "<tbody>" + rows + "</tbody></table></div>";
    }
    status.textContent = "Done." + (skipped.length ? " Skipped " + skipped.length + " slow pattern(s): " + skipped.join(", ") + "." : "");
  }

  function run(values, field, country) {
    var results = [], skipped = [], worker = null, timer = null, current = -1;

    function finish() {
      clearTimeout(timer);
      if (worker) worker.terminate();
      render(IdentifyCore.rank(results, 15), skipped);
    }

    function start(from) {
      worker = new Worker(base + "/assets/identify-worker.js");
      worker.postMessage({ type: "index", index: index });
      worker.onmessage = function (event) {
        var msg = event.data;
        if (msg.type === "progress") {
          current = msg.i;
          clearTimeout(timer);
          timer = setTimeout(function () {
            // This pattern is too slow: stop the worker and continue after it.
            worker.terminate();
            skipped.push(index[current].id);
            if (current + 1 < index.length) start(current + 1);
            else finish();
          }, PATTERN_BUDGET_MS);
        } else if (msg.type === "result") {
          if (msg.result) results.push(msg.result);
        } else if (msg.type === "done") {
          finish();
        }
      };
      worker.postMessage({ type: "run", start: from, values: values, field: field, country: country });
    }

    status.textContent = "Checking " + index.length + " datatypes…";
    start(0);
  }

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    if (!index) return;
    var lines = form.elements.values.value.split(/\r?\n/).map(function (v) { return v.trim(); }).filter(Boolean);
    if (!lines.length) { status.textContent = "Paste at least one value."; return; }
    var values = lines.slice(0, MAX_VALUES).map(function (v) { return v.slice(0, MAX_LENGTH); });
    var country = form.elements.country.value || null;
    run(values, form.elements.field.value.trim(), country);
  });

  status.textContent = "Loading the datatype index…";
  fetch(base + "/identify-index.json")
    .then(function (response) { return response.json(); })
    .then(function (data) {
      index = data;
      status.textContent = "Ready: " + index.length + " datatypes with a regexp or a check digit.";
      form.elements.submit.disabled = false;
    })
    .catch(function () { status.textContent = "Could not load the datatype index."; });
})();
