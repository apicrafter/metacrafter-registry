// Value identification, the same scoring as metacrafter_registry.Registry.identify.
// Shared by the /identify page (in a Web Worker) and the test suite (node).
(function (root) {
  "use strict";

  var SEPARATORS = /[\s-]/g;

  function digitsOf(value) {
    var compact = String(value).replace(/[\s.\-]/g, "");
    return /^\d+$/.test(compact) ? compact.split("").map(Number) : null;
  }

  var CHECKSUMS = {
    luhn: function (v) {
      var d = digitsOf(v);
      if (!d || d.length < 2) return false;
      var total = 0;
      for (var i = 0; i < d.length; i += 1) {
        var x = d[d.length - 1 - i];
        if (i % 2 === 1) { x *= 2; if (x > 9) x -= 9; }
        total += x;
      }
      return total % 10 === 0;
    },
    iban_mod97: function (v) {
      var s = String(v).replace(/[\s.\-]/g, "").toUpperCase();
      if (!/^[A-Z]{2}\d{2}[A-Z0-9]{11,30}$/.test(s)) return false;
      var r = s.slice(4) + s.slice(0, 4);
      var rem = 0;
      for (var i = 0; i < r.length; i += 1) {
        var code = parseInt(r[i], 36);
        var chunk = String(code);
        for (var j = 0; j < chunk.length; j += 1) rem = (rem * 10 + Number(chunk[j])) % 97;
      }
      return rem === 1;
    },
    gtin: function (v) {
      var d = digitsOf(v);
      if (!d || [8, 12, 13, 14].indexOf(d.length) === -1) return false;
      var check = d[d.length - 1], body = d.slice(0, -1), total = 0;
      for (var i = 0; i < body.length; i += 1) total += body[body.length - 1 - i] * (i % 2 === 0 ? 3 : 1);
      return (10 - (total % 10)) % 10 === check;
    },
    isbn13: function (v) { var d = digitsOf(v); return !!d && d.length === 13 && CHECKSUMS.gtin(v); },
    isbn10: function (v) {
      var s = String(v).replace(/[\s.\-]/g, "").toUpperCase();
      if (!/^\d{9}[\dX]$/.test(s)) return false;
      var total = 0;
      for (var i = 0; i < 10; i += 1) total += (10 - i) * (s[i] === "X" ? 10 : Number(s[i]));
      return total % 11 === 0;
    },
    ru_inn: function (v) {
      var d = digitsOf(v);
      if (!d) return false;
      var check = function (w) {
        var t = 0;
        for (var i = 0; i < w.length; i += 1) t += w[i] * d[i];
        return (t % 11) % 10;
      };
      if (d.length === 10) return check([2, 4, 10, 3, 5, 9, 4, 6, 8]) === d[9];
      if (d.length === 12) {
        return check([7, 2, 4, 10, 3, 5, 9, 4, 6, 8]) === d[10] &&
          check([3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8]) === d[11];
      }
      return false;
    },
    ru_snils: function (v) {
      var d = digitsOf(v);
      if (!d || d.length !== 11) return false;
      var total = 0;
      for (var i = 0; i < 9; i += 1) total += d[i] * (9 - i);
      if (total > 101) total %= 101;
      var control = total === 100 || total === 101 ? 0 : total;
      return control === d[9] * 10 + d[10];
    },
    ru_ogrn: function (v) {
      var s = String(v).replace(/[\s.\-]/g, "");
      if (!/^\d+$/.test(s)) return false;
      if (s.length === 13) return (Number(s.slice(0, 12)) % 11) % 10 === Number(s[12]);
      if (s.length === 15) return (Number(s.slice(0, 14)) % 13) % 10 === Number(s[14]);
      return false;
    },
    fr_nir: function (v) {
      var s = String(v).replace(/[\s.\-]/g, "").toUpperCase();
      if (!/^\d{5}(?:\d{2}|2[AB])\d{8}$/.test(s)) return false;
      var dept = s.slice(5, 7) === "2A" ? "19" : s.slice(5, 7) === "2B" ? "18" : s.slice(5, 7);
      var body = s.slice(0, 5) + dept + s.slice(7, 13), rem = 0;
      for (var i = 0; i < body.length; i += 1) rem = (rem * 10 + Number(body[i])) % 97;
      return 97 - rem === Number(s.slice(13));
    },
    at_uid: function (v) {
      var s = String(v).replace(/[\s.\-]/g, "").toUpperCase();
      if (s.indexOf("AT") === 0) s = s.slice(2);
      if (!/^U\d{8}$/.test(s)) return false;
      var d = s.slice(1).split("").map(Number), total = 0;
      for (var i = 0; i < 7; i += 1) {
        var x = d[6 - i];
        if (i % 2 === 1) { x *= 2; if (x > 9) x -= 9; }
        total += x;
      }
      return ((6 - total) % 10 + 10) % 10 === d[7];
    },
    bg_vat: function (v) {
      var s = String(v).replace(/[\s.\-]/g, "").toUpperCase();
      if (s.indexOf("BG") === 0) s = s.slice(2);
      if (!/^\d+$/.test(s)) return false;
      var d = s.split("").map(Number);
      var weighted = function (w) {
        var t = 0;
        for (var i = 0; i < w.length; i += 1) t += w[i] * d[i];
        return t;
      };
      if (d.length === 9) {
        var check = weighted([1, 2, 3, 4, 5, 6, 7, 8]) % 11;
        if (check === 10) check = weighted([3, 4, 5, 6, 7, 8, 9, 10]) % 11;
        return check % 10 === d[8];
      }
      if (d.length === 10) {
        var egn = (weighted([2, 4, 8, 5, 10, 9, 7, 3, 6]) % 11) % 10;
        var pnf = weighted([21, 19, 17, 13, 11, 9, 7, 3, 1]) % 10;
        var other = (((11 - weighted([4, 3, 2, 7, 6, 5, 4, 3, 2])) % 11) + 11) % 11;
        return d[9] === egn || d[9] === pnf || d[9] === other;
      }
      return false;
    },
    no_fnr: function (v) {
      var d = digitsOf(v);
      if (!d || d.length !== 11) return false;
      var check = function (w) {
        var t = 0;
        for (var i = 0; i < w.length; i += 1) t += w[i] * d[i];
        return (11 - (t % 11)) % 11;
      };
      return check([3, 7, 6, 1, 8, 9, 4, 5, 2]) === d[9] &&
        check([5, 4, 3, 2, 7, 6, 5, 4, 3, 2]) === d[10];
    },
    it_codicefiscale: function (v) {
      var s = String(v).replace(/[\s.\-]/g, "").toUpperCase();
      if (!/^[A-Z]{6}[0-9LMNP-V]{2}[ABCDEHLMPRST][0-9LMNP-V]{2}[A-Z][0-9LMNP-V]{3}[A-Z]$/.test(s)) return false;
      var odd = [1, 0, 5, 7, 9, 13, 15, 17, 19, 21, 2, 4, 18, 20, 11, 3, 6, 8, 12, 14, 16, 10, 22, 25, 24, 23];
      var total = 0;
      for (var i = 0; i < 15; i += 1) {
        var c = s[i], n = /\d/.test(c) ? Number(c) : c.charCodeAt(0) - 65;
        total += i % 2 === 0 ? odd[n] : n;
      }
      return String.fromCharCode(65 + (total % 26)) === s[15];
    },
    it_iva: function (v) {
      var s = String(v).replace(/[\s.\-]/g, "").toUpperCase();
      if (s.indexOf("IT") === 0) s = s.slice(2);
      if (!/^\d{11}$/.test(s) || Number(s.slice(0, 7)) === 0) return false;
      var office = s.slice(7, 10);
      if (!((office >= "001" && office <= "100") || ["120", "121", "888", "999"].indexOf(office) !== -1)) return false;
      return CHECKSUMS.luhn(s);
    },
    fi_hetu: function (v) {
      var s = String(v).replace(/\s/g, "").toUpperCase();
      var m = /^(\d{6})[-+A-FU-Y](\d{3})([0-9A-FHJ-NPR-Y])$/.exec(s);
      if (!m) return false;
      return "0123456789ABCDEFHJKLMNPRSTUVWXY"[Number(m[1] + m[2]) % 31] === m[3];
    },
    es_dni: function (v) {
      var s = String(v).replace(/[\s.\-]/g, "").toUpperCase();
      if (!/^\d{8}[A-Z]$/.test(s)) return false;
      return "TRWAGMYFPDXBNJZSQVHLCKE"[Number(s.slice(0, 8)) % 23] === s[8];
    }
  };

  function tokens(text) {
    var spaced = String(text || "").replace(/([a-z0-9])([A-Z])/g, "$1 $2").toLowerCase();
    var out = {};
    (spaced.match(/[a-z0-9]+/g) || []).forEach(function (t) { out[t] = true; });
    return out;
  }

  function compile(record) {
    if (!record.re) return null;
    try {
      return new RegExp("^(?:" + record.re + ")$", record.f || "");
    } catch (e) {
      return null;
    }
  }

  function fullmatch(re, value) {
    if (re.test(value)) return true;
    var compact = value.replace(SEPARATORS, "");
    return compact !== value && re.test(compact);
  }

  function nameSimilarity(record, field) {
    var f = String(field || "").trim().toLowerCase();
    if (!f) return 0;
    var aliases = record.a || [];
    if (f === record.id || aliases.indexOf(f) !== -1) return 1;
    var ft = tokens(field), fkeys = Object.keys(ft);
    if (!fkeys.length) return 0;
    var best = 0;
    [record.id].concat(aliases).forEach(function (cid) {
      var compact = cid.replace(/_/g, "");
      fkeys.forEach(function (t) { if (t.length >= 4 && compact.indexOf(t) !== -1) best = 0.6; });
    });
    [record.id, record.n].concat(aliases, record.t || []).forEach(function (cand) {
      var ct = tokens(cand), ckeys = Object.keys(ct);
      if (!ckeys.length) return;
      var inter = fkeys.filter(function (t) { return ct[t]; }).length;
      var union = Object.keys(Object.assign({}, ft, ct)).length;
      best = Math.max(best, inter / union);
    });
    return best;
  }

  // Score one record; returns null when there is no evidence at all.
  function scoreRecord(record, re, values, field, country) {
    var hitRate = null;
    if (values.length && re) {
      var hits = 0;
      for (var i = 0; i < values.length; i += 1) if (fullmatch(re, values[i])) hits += 1;
      hitRate = hits / values.length;
    }
    var checksum = null;
    if (values.length && record.ck && CHECKSUMS[record.ck]) {
      var passed = 0;
      for (var j = 0; j < values.length; j += 1) if (CHECKSUMS[record.ck](values[j])) passed += 1;
      checksum = { algorithm: record.ck, pass_rate: passed / values.length };
    }
    var similarity = field ? nameSimilarity(record, field) : 0;
    if (!(hitRate || (checksum && checksum.pass_rate) || similarity >= 0.5)) return null;
    var specificity = 1 - (record.b || 0);
    var score = 60 * (hitRate || 0) * specificity + 25 * similarity;
    if (checksum) score += 25 * checksum.pass_rate;
    if (country && record.c && record.c.length) score += record.c.indexOf(country) !== -1 ? 5 : -10;
    if (record.s === "draft") score -= 5;
    return {
      id: record.id,
      name: record.n,
      status: record.s,
      is_pii: record.p,
      score: Math.max(0, Math.min(100, Math.round(score))),
      regexp_hit_rate: hitRate,
      checksum: checksum,
      field_name_similarity: similarity
    };
  }

  function rank(results, limit) {
    results.sort(function (x, y) {
      return y.score - x.score || (x.status !== "stable") - (y.status !== "stable") ||
        (x.id < y.id ? -1 : x.id > y.id ? 1 : 0);
    });
    return results.slice(0, limit || 10);
  }

  // Synchronous version (tests, small inputs). The page uses the worker loop instead.
  function identify(index, values, field, country, limit) {
    var samples = values.map(function (v) { return String(v).trim(); }).filter(Boolean);
    var c = country ? String(country).toUpperCase() : null;
    var results = [];
    index.forEach(function (record) {
      var r = scoreRecord(record, compile(record), samples, field, c);
      if (r) results.push(r);
    });
    return rank(results, limit);
  }

  var api = {
    CHECKSUMS: CHECKSUMS,
    compile: compile,
    scoreRecord: scoreRecord,
    rank: rank,
    identify: identify
  };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.IdentifyCore = api;
})(typeof self !== "undefined" ? self : this);
