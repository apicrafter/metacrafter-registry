// Runs regexps off the main thread. It reports progress after every record so
// that the page can stop it if one pattern takes too long (catastrophic
// backtracking) and continue with the next record. It returns how each
// record's regexp matches the values; the page scores the records once all of
// them are matched, because a compact-form match depends on the other regexps.
/* global IdentifyCore */
importScripts("identify-core.js");

var index = [];

self.onmessage = function (event) {
  var msg = event.data;
  if (msg.type === "index") {
    index = msg.index;
    return;
  }
  if (msg.type !== "run") return;
  var values = msg.values;
  for (var i = msg.start; i < index.length; i += 1) {
    self.postMessage({ type: "progress", i: i });
    var re = IdentifyCore.compile(index[i]);
    self.postMessage({ type: "result", i: i, matched: re ? IdentifyCore.matchValues(re, values) : null });
  }
  self.postMessage({ type: "done" });
};
