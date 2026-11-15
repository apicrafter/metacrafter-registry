// "Test a value" on a record page: checks one value against this record's
// regexp and check-digit algorithm. Nothing leaves the browser.
/* global IdentifyCore */
(function () {
  "use strict";

  var form = document.getElementById("value-test");
  if (!form || typeof IdentifyCore === "undefined") return;
  var output = document.getElementById("value-test-result");
  var pattern = form.getAttribute("data-re");
  var checksum = form.getAttribute("data-checksum");
  var re = pattern === null ? null : IdentifyCore.compile({ re: pattern, f: form.getAttribute("data-flags") });
  var check = checksum ? IdentifyCore.CHECKSUMS[checksum] : null;
  // Without a usable regexp or a known algorithm there is nothing to test.
  if (!re && !check) return;

  form.hidden = false;
  form.addEventListener("submit", function (event) {
    event.preventDefault();
    var value = form.elements.value.value.trim();
    if (!value) { output.textContent = "Enter a value."; return; }
    var parts = [];
    if (re) parts.push(re.test(value) ? "Matches the regular expression." : "Does not match the regular expression.");
    if (check) parts.push(check(value) ? "The check digit is valid." : "The check digit is not valid.");
    parts.push("A match does not prove that the value exists or belongs to anyone.");
    output.textContent = parts.join(" ");
  });
})();
