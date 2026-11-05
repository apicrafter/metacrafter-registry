// Value identification, the same scoring as metacrafter_registry.Registry.identify.
// Shared by the /identify page (in a Web Worker) and the test suite (node).
(function (root) {
  "use strict";

  var SEPARATORS = /[\s-]/g;

  function digitsOf(value) {
    var compact = String(value).replace(/[\s.\-]/g, "");
    return /^\d+$/.test(compact) ? compact.split("").map(Number) : null;
  }

  function isPrime(n) {
    for (var p = 2; p * p <= n; p += 1) if (n % p === 0) return false;
    return n > 1;
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
    gs1_mod10: function (v) {
      var d = digitsOf(v);
      if (!d || d.length < 2) return false;
      var check = d[d.length - 1], body = d.slice(0, -1), total = 0;
      for (var i = 0; i < body.length; i += 1) total += body[body.length - 1 - i] * (i % 2 === 0 ? 3 : 1);
      return (10 - (total % 10)) % 10 === check;
    },
    gtin: function (v) {
      var d = digitsOf(v);
      if (!d || [8, 12, 13, 14].indexOf(d.length) === -1) return false;
      return CHECKSUMS.gs1_mod10(v);
    },
    gs1_checkpair: function (v) {
      var cset82 = "!\"%&'()*+,-./0123456789:;<=>?ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqrstuvwxyz";
      var cset32 = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ";
      var s = String(v).trim();
      if (s.length < 2) return false;
      var body = s.slice(0, -2), total = 0, prime = 1;
      for (var i = body.length - 1; i >= 0; i -= 1) {
        var weight = cset82.indexOf(body[i]);
        if (weight === -1) return false;
        do { prime += 1; } while (!isPrime(prime));
        total += weight * prime;
      }
      total %= 1021;
      return s.slice(-2) === cset32[total >> 5] + cset32[total & 31];
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
    },
    pl_nip: function (v) {
      var s = stripPrefix(v, "PL");
      if (!/^\d{10}$/.test(s)) return false;
      var w = [6, 5, 7, 2, 3, 4, 5, 6, 7], t = 0;
      for (var i = 0; i < 9; i += 1) t += w[i] * Number(s[i]);
      return t % 11 === Number(s[9]);
    },
    sk_dph: function (v) {
      var s = stripPrefix(v, "SK");
      if (!/^[1-9]\d{9}$/.test(s)) return false;
      var rem = 0;
      for (var i = 0; i < s.length; i += 1) rem = (rem * 10 + Number(s[i])) % 11;
      return rem === 0;
    },
    si_ddv: function (v) {
      var s = stripPrefix(v, "SI");
      if (!/^[1-9]\d{7}$/.test(s)) return false;
      var t = 0;
      for (var i = 0; i < 7; i += 1) t += (8 - i) * Number(s[i]);
      var check = 11 - (t % 11);
      return check !== 11 && check % 10 === Number(s[7]);
    },
    se_vat: function (v) {
      var s = stripPrefix(v, "SE");
      return /^\d{10}01$/.test(s) && CHECKSUMS.luhn(s.slice(0, 10));
    },
    kz_iin_bin: function (v) {
      var d = digitsOf(v);
      if (!d || d.length !== 12) return false;
      var weighted = function (w) {
        var t = 0;
        for (var i = 0; i < 11; i += 1) t += w[i] * d[i];
        return t % 11;
      };
      var check = weighted([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]);
      if (check === 10) check = weighted([3, 4, 5, 6, 7, 8, 9, 10, 11, 1, 2]);
      return check !== 10 && check === d[11];
    },
    iso7064_mod97_10: function (v) {
      var s = String(v).replace(/[\s.\-]/g, "").toUpperCase();
      if (!/^[0-9A-Z]{3,}$/.test(s)) return false;
      var rem = 0;
      for (var i = 0; i < s.length; i += 1) {
        var chunk = String(parseInt(s[i], 36));
        for (var j = 0; j < chunk.length; j += 1) rem = (rem * 10 + Number(chunk[j])) % 97;
      }
      return rem === 1;
    },
    de_ustidnr: function (v) {
      var s = stripPrefix(v, "DE");
      return /^[1-9]\d{8}$/.test(s) && mod11_10(s);
    },
    de_widnr: function (v) {
      var s = stripPrefix(v, "DE");
      return /^\d{14}$/.test(s) && CHECKSUMS.de_ustidnr(s.slice(0, 9));
    },
    de_idnr: function (v) {
      var d = digitsOf(v);
      if (!d || d.length !== 11 || d[0] === 0) return false;
      var counts = {}, repeated = [], i;
      for (i = 0; i < 10; i += 1) counts[d[i]] = (counts[d[i]] || 0) + 1;
      for (var k in counts) if (counts[k] > 1) repeated.push(counts[k]);
      if (repeated.length !== 1 || (repeated[0] !== 2 && repeated[0] !== 3)) return false;
      for (i = 0; i < 8; i += 1) if (d[i] === d[i + 1] && d[i + 1] === d[i + 2]) return false;
      return mod11_10(d.join(""));
    },
    de_rvnr: function (v) {
      var s = String(v).replace(/[\s.\-]/g, "").toUpperCase();
      if (!/^\d{8}[A-Z]\d{3}$/.test(s)) return false;
      var letter = s.charCodeAt(8) - 64;
      var n = s.slice(0, 8) + (letter < 10 ? "0" : "") + letter + s.slice(9, 11);
      var w = [2, 1, 2, 5, 7, 1, 2, 1, 2, 1, 2, 1], t = 0;
      for (var i = 0; i < 12; i += 1) { var p = w[i] * Number(n[i]); t += Math.floor(p / 10) + (p % 10); }
      return t % 10 === Number(s[11]);
    },
    de_kvnr: function (v) {
      var s = String(v).replace(/[\s.\-]/g, "").toUpperCase();
      if (!/^[A-Z]\d{9}$/.test(s)) return false;
      var letter = s.charCodeAt(0) - 64;
      var n = (letter < 10 ? "0" : "") + letter + s.slice(1, 9), t = 0;
      for (var i = 0; i < 10; i += 1) { var p = (1 + (i % 2)) * Number(n[i]); t += Math.floor(p / 10) + (p % 10); }
      return t % 10 === Number(s[9]);
    },
    de_ik: function (v) {
      var d = digitsOf(v);
      if (!d || d.length !== 9) return false;
      var t = 0;
      for (var i = 0; i < 6; i += 1) { var p = d[2 + i] * (i % 2 === 0 ? 2 : 1); t += p > 9 ? p - 9 : p; }
      return t % 10 === d[8];
    },
    de_lanr: function (v) {
      var d = digitsOf(v);
      if (!d || d.length !== 9) return false;
      var t = 0;
      for (var i = 0; i < 6; i += 1) t += d[i] * (i % 2 === 0 ? 4 : 9);
      return (10 - (t % 10)) % 10 === d[6];
    },
    de_pzn: function (v) {
      var s = stripPrefix(v, "PZN");
      if (!/^\d{7,8}$/.test(s)) return false;
      if (s.length === 7) s = "0" + s;
      var t = 0;
      for (var i = 0; i < 7; i += 1) t += (i + 1) * Number(s[i]);
      var check = t % 11;
      return check !== 10 && check === Number(s[7]);
    },
    de_fsnr: function (v) {
      var s = String(v).replace(/[\s.\-]/g, "").toUpperCase();
      if (!/^[0-9A-Z]{9}[0-9X][0-9A-Z]$/.test(s)) return false;
      var t = 0;
      for (var i = 0; i < 9; i += 1) t += (9 - i) * parseInt(s[i], 36);
      var check = t % 11;
      return s[9] === (check === 10 ? "X" : String(check));
    },
    cz_ico: function (v) {
      var d = digitsOf(v);
      if (!d || d.length !== 8) return false;
      var t = 0;
      for (var i = 0; i < 7; i += 1) t += (8 - i) * d[i];
      return (11 - (t % 11)) % 10 === d[7];
    },
    cz_rc: function (v) {
      var s = String(v).replace(/[\s.\-\/]/g, "");
      if (!/^\d{9,10}$/.test(s)) return false;
      if (s.length === 9) {
        var yy = Number(s.slice(0, 2));
        return yy < 54 || yy > 79;
      }
      var rem = 0;
      for (var i = 0; i < 9; i += 1) rem = (rem * 10 + Number(s[i])) % 11;
      return rem % 10 === Number(s[9]);
    },
    cz_dic: function (v) {
      var s = stripPrefix(v, "CZ").replace(/\//g, "");
      if (!/^\d{8,10}$/.test(s)) return false;
      if (s.length === 8) return s[0] !== "9" && CHECKSUMS.cz_ico(s);
      if (s.length === 9 && s[0] === "6") {
        var t = 0;
        for (var i = 0; i < 7; i += 1) t += (8 - i) * Number(s[i + 1]);
        var check = (((8 - ((10 - (t % 11)) % 11)) % 10) + 10) % 10;
        return check === Number(s[8]);
      }
      return CHECKSUMS.cz_rc(s);
    },
    cz_bank_account: function (v) {
      var m = /^(?:(\d{1,6})-)?(\d{2,10})\/\d{4}$/.exec(String(v).replace(/\s/g, ""));
      if (!m || m[2].replace(/0/g, "").length < 2) return false;
      var w = [6, 3, 7, 9, 10, 5, 8, 4, 2, 1];
      var part = function (p) {
        p = ("0000000000" + p).slice(-10);
        var t = 0;
        for (var i = 0; i < 10; i += 1) t += w[i] * Number(p[i]);
        return t % 11 === 0;
      };
      return part(m[1] || "0") && part(m[2]);
    },
    cz_isds: function (v) {
      var a = "abcdefghijkmnpqrstuvwxyz23456789";
      var s = String(v).replace(/[\s.\-]/g, "").toLowerCase();
      if (!/^[a-km-np-z2-9]{7}$/.test(s)) return false;
      var t = 0;
      for (var i = 0; i < 6; i += 1) {
        var n = a.indexOf(s[i]) * (i % 2 === 1 ? 2 : 1);
        t += Math.floor(n / 32) + (n % 32);
      }
      return a[(32 - (t % 32)) % 32] === s[6];
    }
  };

  // ISO 7064 MOD 11,10 over a digit string that ends with its check digit.
  function mod11_10(s) {
    var check = 5;
    for (var i = 0; i < s.length; i += 1) check = (((check || 10) * 2) % 11 + Number(s[i])) % 10;
    return check === 1;
  }

  function stripPrefix(value, prefix) {
    var s = String(value).replace(/[\s.\-]/g, "").toUpperCase();
    return s.indexOf(prefix) === 0 ? s.slice(prefix.length) : s;
  }

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

  // How a regexp matches each value: RAW when it matches the value as written,
  // COMPACT when it matches only once spaces and hyphens are removed
  // ("4111 1111 1111 1111"), 0 otherwise.
  var RAW = 1, COMPACT = 2;
  // In the score a COMPACT hit counts this much of a RAW hit (_COMPACT_WEIGHT
  // in client.py): a match of the value as written is stronger evidence. A
  // COMPACT hit whose check digit passes counts as a RAW one.
  var COMPACT_WEIGHT = 0.5;

  function matchValues(re, values) {
    return values.map(function (value) {
      if (re.test(value)) return RAW;
      var compact = value.replace(SEPARATORS, "");
      return compact !== value && re.test(compact) ? COMPACT : 0;
    });
  }

  // Per value, the broadness of the most specific regexp that matches it as
  // written (Infinity when none does). matches[i] is matchValues() of index[i],
  // or null/undefined when that record has no regexp or its pattern was skipped.
  function claims(index, matches, count) {
    var out = [];
    for (var j = 0; j < count; j += 1) out.push(Infinity);
    for (var i = 0; i < index.length; i += 1) {
      var m = matches[i];
      if (!m) continue;
      var b = index[i].b || 0;
      for (var k = 0; k < count; k += 1) if (m[k] === RAW && b < out[k]) out[k] = b;
    }
    return out;
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

  // Score one record; returns null when there is no evidence at all. matched is
  // matchValues() of the record's regexp (null without one) and claimed is
  // claims() over the whole index: a compact-form match counts only when no
  // regexp that is at least as specific matches the value as written, and then
  // counts COMPACT_WEIGHT in the score unless the check digit passes.
  function scoreRecord(record, matched, values, field, country, claimed) {
    var checks = null, checksum = null;
    if (values.length && record.ck && CHECKSUMS[record.ck]) {
      var passed = 0;
      checks = values.map(function (v) { return CHECKSUMS[record.ck](v); });
      for (var j = 0; j < checks.length; j += 1) if (checks[j]) passed += 1;
      checksum = { algorithm: record.ck, pass_rate: passed / values.length };
    }
    var hitRate = null, weightedRate = 0;
    if (values.length && matched) {
      var own = record.b || 0, hits = 0, weight = 0;
      for (var i = 0; i < values.length; i += 1) {
        if (matched[i] === RAW) {
          hits += 1;
          weight += 1;
        } else if (matched[i] === COMPACT && claimed[i] > own) {
          hits += 1;
          weight += checks && checks[i] ? 1 : COMPACT_WEIGHT;
        }
      }
      hitRate = hits / values.length;
      weightedRate = weight / values.length;
    }
    var similarity = field ? nameSimilarity(record, field) : 0;
    if (!(hitRate || (checksum && checksum.pass_rate) || similarity >= 0.5)) return null;
    var specificity = 1 - (record.b || 0);
    var score = 60 * weightedRate * specificity + 25 * similarity;
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
    var matches = index.map(function (record) {
      var re = compile(record);
      return re ? matchValues(re, samples) : null;
    });
    var claimed = claims(index, matches, samples.length);
    var results = [];
    index.forEach(function (record, i) {
      var r = scoreRecord(record, matches[i], samples, field, c, claimed);
      if (r) results.push(r);
    });
    return rank(results, limit);
  }

  var api = {
    CHECKSUMS: CHECKSUMS,
    compile: compile,
    matchValues: matchValues,
    claims: claims,
    scoreRecord: scoreRecord,
    rank: rank,
    identify: identify
  };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.IdentifyCore = api;
})(typeof self !== "undefined" ? self : this);
