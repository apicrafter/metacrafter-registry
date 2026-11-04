// Runs regexps off the main thread. It reports progress after every record so
// that the page can stop it if one pattern takes too long (catastrophic
// backtracking) and continue with the next record.
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
    var record = index[i];
    var result = IdentifyCore.scoreRecord(record, IdentifyCore.compile(record), values, msg.field, msg.country);
    self.postMessage({ type: "result", i: i, result: result });
  }
  self.postMessage({ type: "done" });
};
