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

  // SHA-256 (FIPS 180-4) of an array of bytes, for Base58Check.
  var SHA256_K = [
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2
  ];

  function sha256(bytes) {
    var h = [0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19];
    var msg = bytes.slice(), bits = bytes.length * 8, w = new Array(64), i, t;
    msg.push(0x80);
    while (msg.length % 64 !== 56) msg.push(0);
    msg.push(0, 0, 0, 0, (bits >>> 24) & 0xff, (bits >>> 16) & 0xff, (bits >>> 8) & 0xff, bits & 0xff);
    var rotr = function (x, n) { return (x >>> n) | (x << (32 - n)); };
    for (var off = 0; off < msg.length; off += 64) {
      for (t = 0; t < 16; t += 1) {
        i = off + 4 * t;
        w[t] = (msg[i] << 24) | (msg[i + 1] << 16) | (msg[i + 2] << 8) | msg[i + 3];
      }
      for (t = 16; t < 64; t += 1) {
        var s0 = rotr(w[t - 15], 7) ^ rotr(w[t - 15], 18) ^ (w[t - 15] >>> 3);
        var s1 = rotr(w[t - 2], 17) ^ rotr(w[t - 2], 19) ^ (w[t - 2] >>> 10);
        w[t] = (w[t - 16] + s0 + w[t - 7] + s1) | 0;
      }
      var a = h[0], b = h[1], c = h[2], d = h[3], e = h[4], f = h[5], g = h[6], k = h[7];
      for (t = 0; t < 64; t += 1) {
        var t1 = (k + (rotr(e, 6) ^ rotr(e, 11) ^ rotr(e, 25)) + ((e & f) ^ (~e & g)) + SHA256_K[t] + w[t]) | 0;
        var t2 = ((rotr(a, 2) ^ rotr(a, 13) ^ rotr(a, 22)) + ((a & b) ^ (a & c) ^ (b & c))) | 0;
        k = g; g = f; f = e; e = (d + t1) | 0; d = c; c = b; b = a; a = (t1 + t2) | 0;
      }
      h[0] = (h[0] + a) | 0; h[1] = (h[1] + b) | 0; h[2] = (h[2] + c) | 0; h[3] = (h[3] + d) | 0;
      h[4] = (h[4] + e) | 0; h[5] = (h[5] + f) | 0; h[6] = (h[6] + g) | 0; h[7] = (h[7] + k) | 0;
    }
    var out = [];
    for (i = 0; i < 8; i += 1) out.push((h[i] >>> 24) & 0xff, (h[i] >>> 16) & 0xff, (h[i] >>> 8) & 0xff, h[i] & 0xff);
    return out;
  }

  var BASE58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz";
  var BECH32 = "qpzry9x8gf2tvdw0s3jn54khce6mua7l";
  var BECH32_GENERATOR = [0x3b6a57b2, 0x26508e6d, 0x1ea119fa, 0x3d4233dd, 0x2a1462b3];

  function bech32Verify(v, constant) {
    // The human-readable part keeps its hyphens and dots (age secret keys start
    // with AGE-SECRET-KEY-1); separators are ignored in the data part only.
    var t = String(v).replace(/\s/g, ""), p = t.lastIndexOf("1");
    var s = p >= 0 ? t.slice(0, p + 1) + t.slice(p + 1).replace(/[.\-]/g, "") : t;
    if (!/^[\x21-\x7e]+$/.test(s)) return false;
    if (s !== s.toLowerCase() && s !== s.toUpperCase()) return false;
    s = s.toLowerCase();
    var pos = s.lastIndexOf("1"), values = [], i;
    if (pos < 1 || s.length - pos - 1 < 6) return false;
    for (i = 0; i < pos; i += 1) values.push(s.charCodeAt(i) >> 5);
    values.push(0);
    for (i = 0; i < pos; i += 1) values.push(s.charCodeAt(i) & 31);
    for (i = pos + 1; i < s.length; i += 1) {
      var d = BECH32.indexOf(s.charAt(i));
      if (d < 0) return false;
      values.push(d);
    }
    var chk = 1;
    for (i = 0; i < values.length; i += 1) {
      var top = chk >>> 25;
      chk = ((chk & 0x1ffffff) << 5) ^ values[i];
      for (var j = 0; j < 5; j += 1) if ((top >>> j) & 1) chk ^= BECH32_GENERATOR[j];
    }
    return chk === constant;
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
    issn: function (v) {
      var s = String(v).replace(/[\s.\-]/g, "").toUpperCase();
      if (!/^\d{7}[\dX]$/.test(s)) return false;
      var total = 0;
      for (var i = 0; i < 8; i += 1) total += (8 - i) * (s[i] === "X" ? 10 : Number(s[i]));
      return total % 11 === 0;
    },
    ismn: function (v) {
      var s = String(v).replace(/[\s.\-]/g, "").toUpperCase();
      if (/^M\d{9}$/.test(s)) s = "9790" + s.slice(1);
      return /^9790\d{9}$/.test(s) && CHECKSUMS.gtin(s);
    },
    iso7064_mod11_2: function (v) {
      var s = String(v).replace(/[\s.\-]/g, "").toUpperCase();
      if (!/^\d+[\dX]$/.test(s)) return false;
      var total = 0;
      for (var i = 0; i < s.length - 1; i += 1) total = ((total + Number(s[i])) * 2) % 11;
      var check = (12 - total) % 11;
      return s[s.length - 1] === (check === 10 ? "X" : String(check));
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
    ru_inn_padded: function (v) {
      var s = String(v).replace(/[\s.\-]/g, "");
      return s.length === 12 && s.slice(0, 2) === "00" && CHECKSUMS.ru_inn(s.slice(2));
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
      // Sign digit, first year of issue and modulus: OGRN (13) or OGRNIP (15).
      var spec = s.length === 13 ? ["15", 2, 11] : s.length === 15 ? ["3", 4, 13] : null;
      if (!spec || spec[0].indexOf(s[0]) < 0) return false;
      var year = Number(s.slice(1, 3));
      if (year < spec[1] || year > new Date().getFullYear() % 100) return false;
      if (s.slice(3, 5) === "00") return false;
      return (Number(s.slice(0, -1)) % spec[2]) % 10 === Number(s[s.length - 1]);
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
    it_aic: function (v) {
      var s = String(v).replace(/[\s.\-]/g, "").toUpperCase();
      var b32 = "0123456789BCDFGHJKLMNPQRSTUVWXYZ";
      if (/^[0-9B-DF-HJ-NP-Z]{6}$/.test(s)) {
        var n = 0;
        for (var j = 0; j < 6; j += 1) n = n * 32 + b32.indexOf(s[j]);
        s = String(n);
        while (s.length < 9) s = "0" + s;
      }
      if (!/^0\d{8}$/.test(s)) return false;
      var t = 0;
      for (var i = 0; i < 8; i += 1) {
        var p = Number(s[i]) * (i % 2 === 0 ? 1 : 2);
        t += Math.floor(p / 10) + (p % 10);
      }
      return t % 10 === Number(s[8]);
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
    base58check: function (v) {
      var s = String(v).replace(/[\s.\-]/g, ""), bytes = [], i, j;
      if (!s) return false;
      for (i = 0; i < s.length; i += 1) {
        var carry = BASE58.indexOf(s.charAt(i));
        if (carry < 0) return false;
        for (j = 0; j < bytes.length; j += 1) {
          carry += bytes[j] * 58;
          bytes[j] = carry & 0xff;
          carry >>= 8;
        }
        while (carry > 0) { bytes.push(carry & 0xff); carry >>= 8; }
      }
      var raw = [];
      for (i = 0; i < s.length && s.charAt(i) === "1"; i += 1) raw.push(0);
      raw = raw.concat(bytes.reverse());
      if (raw.length < 5) return false;
      var hash = sha256(sha256(raw.slice(0, raw.length - 4)));
      for (i = 0; i < 4; i += 1) if (hash[i] !== raw[raw.length - 4 + i]) return false;
      return true;
    },
    bech32: function (v) { return bech32Verify(v, 1); },
    bech32m: function (v) { return bech32Verify(v, 0x2bc830a3); },
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
    ror: function (v) {
      var s = String(v).replace(/^(?:https?:\/\/)?ror\.org\//i, "").toLowerCase();
      var m = /^0([0-9a-hjkmnp-tv-z]{6})([0-9]{2})$/.exec(s);
      if (!m) return false;
      var n = 0;
      for (var i = 0; i < 6; i += 1) n = n * 32 + "0123456789abcdefghjkmnpqrstvwxyz".indexOf(m[1][i]);
      return Number(m[2]) === 98 - ((n * 100) % 97);
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
    },
    be_kbo: function (v) {
      var s = stripPrefix(v, "BE");
      if (s.length === 9) s = "0" + s;
      if (!/^\d{10}$/.test(s)) return false;
      return 97 - (Number(s.slice(0, 8)) % 97) === Number(s.slice(8));
    },
    be_nn: function (v) {
      return bePersonNumber(v, function (m) { return m <= 12; });
    },
    be_bis: function (v) {
      return bePersonNumber(v, function (m) { return (m >= 20 && m <= 32) || (m >= 40 && m <= 52); });
    },
    be_insz: function (v) {
      return CHECKSUMS.be_nn(v) || CHECKSUMS.be_bis(v);
    },
    be_mod97: function (v) {
      var s = String(v).replace(/[\s.\-\/+*]/g, "");
      if (!/^\d{12}$/.test(s)) return false;
      return (Number(s.slice(0, 10)) % 97 || 97) === Number(s.slice(10));
    },
    nl_bsn: function (v) {
      var d = digitsOf(v);
      if (!d || (d.length !== 8 && d.length !== 9) || !/[1-9]/.test(d.join(""))) return false;
      if (d.length === 8) d.unshift(0);
      return elfproef(d) === 0;
    },
    nl_onderwijsnummer: function (v) {
      var d = digitsOf(v);
      if (!d || d.length !== 9 || d[0] !== 1 || d[1] !== 0) return false;
      return elfproef(d) === 5;
    },
    nl_btw: function (v) {
      var s = stripPrefix(v, "NL");
      if (!/^\d{9}B\d{2}$/.test(s) || s.slice(10) === "00") return false;
      return CHECKSUMS.nl_bsn(s.slice(0, 9)) || CHECKSUMS.iso7064_mod97_10("NL" + s);
    }
  };

  // Dutch 11-proef sum of 9 digits: weights 9 down to 2, the last digit subtracted, modulo 11.
  function elfproef(d) {
    var t = -d[8];
    for (var i = 0; i < 8; i += 1) t += (9 - i) * d[i];
    return ((t % 11) + 11) % 11;
  }

  // Belgian national register and BIS numbers: YYMMDD, serial, 2 check digits.
  function bePersonNumber(v, monthOk) {
    var s = String(v).replace(/[\s.\-]/g, "");
    if (!/^\d{11}$/.test(s) || !monthOk(Number(s.slice(2, 4)))) return false;
    var nine = Number(s.slice(0, 9));
    var check = Number(s.slice(9));
    return check === 97 - (nine % 97) || check === 97 - ((2e9 + nine) % 97);
  }

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

  // Russian noun and adjective endings, longest first: _RU_ENDINGS in client.py,
  // the same list in the same order.
  var RU_ENDINGS = (
    "иями ями ами ими ыми ией иям ием иях его ого ему ому " +
    "ев ов ие ье еи ии ей ой ий ый ям ем ам ом ах ях ию ью ия ья ее ые ое им ым их ых ую юю " +
    "ая яя ою ею а я о е и ы у ю ь й"
  ).split(" ");
  var RU_MIN_STEM = 4; // a shorter stem would merge unrelated words ("пол" and "поле")

  // A word without its Russian case ending, with ё read as е; other words as is.
  function stem(word) {
    if (!/^[а-яё]+$/.test(word)) return word;
    word = word.replace(/ё/g, "е");
    for (var i = 0; i < RU_ENDINGS.length; i += 1) {
      var ending = RU_ENDINGS[i];
      if (word.length - ending.length >= RU_MIN_STEM &&
          word.slice(-ending.length) === ending) return word.slice(0, -ending.length);
    }
    return word;
  }

  // The lowercased words of a field name or a record name, in any script: runs of
  // letters, combining marks and digits, camelCase split ("СерийныйНомер"), Russian
  // case endings removed. _tokens in client.py is the same.
  function tokens(text) {
    var spaced = String(text || "")
      .normalize("NFC")
      .replace(/([\p{Lowercase}\p{Nd}])(?=\p{Uppercase})/gu, "$1 ")
      .toLowerCase();
    var out = Object.create(null); // no inherited keys: "constructor" is a token too
    (spaced.match(/[\p{L}\p{M}\p{N}]+/gu) || []).forEach(function (t) { out[stem(t)] = true; });
    return out;
  }

  // Two capital letters in parentheses are as often a qualifier ("(EU)", "(UK)")
  // or a short common word as an abbreviation of the name.
  var ABBREVIATION_MIN_LEN = 3;

  // Like Python's str.isupper(): a cased letter and no lowercase one.
  function isUpper(text) {
    return text === text.toUpperCase() && text !== text.toLowerCase();
  }

  // The abbreviations that a name gives in parentheses, as tokens(): one word of
  // at least three characters with no lowercase letter, alone or in a list
  // separated by commas or semicolons ("Номер (ОГРН, ОГРНИП)" gives огрн and
  // огрнип). _abbreviations in client.py is the same.
  function abbreviations(text) {
    var out = Object.create(null);
    (String(text || "").match(/\([^()]*\)/g) || []).forEach(function (group) {
      group.slice(1, -1).split(/[,;]/).forEach(function (item) {
        item = item.trim();
        var words = Object.keys(tokens(item));
        if (words.length === 1 && item.length >= ABBREVIATION_MIN_LEN && isUpper(item)) {
          out[words[0]] = true;
        }
      });
    });
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

  function hasAscii(word) {
    return /[\x00-\x7f]/.test(word);
  }

  function nameSimilarity(record, field) {
    var f = String(field || "").trim().toLowerCase();
    if (!f) return 0;
    var aliases = record.a || [];
    if (f === record.id || aliases.indexOf(f) !== -1) return 1;
    var ft = tokens(field), fkeys = Object.keys(ft);
    if (!fkeys.length) return 0;
    // A field named by the abbreviations that a name gives in parentheses names
    // the datatype itself: "ОГРН" or "ОГРН/ОГРНИП" (_name_similarity in client.py).
    var names = [record.n].concat(record.t || []);
    for (var i = 0; i < names.length; i += 1) {
      var abbr = abbreviations(names[i]);
      if (fkeys.every(function (t) { return abbr[t]; })) return 1;
    }
    var best = 0;
    [record.id].concat(aliases).forEach(function (cid) {
      var compact = cid.replace(/_/g, "");
      fkeys.forEach(function (t) { if (t.length >= 4 && compact.indexOf(t) !== -1) best = 0.6; });
    });
    // A field name in Latin letters is compared with the Latin words of each
    // name only; a Latin word has an ASCII letter or digit (_name_similarity in
    // client.py).
    var latinField = fkeys.every(hasAscii);
    [record.id, record.n].concat(aliases, record.t || []).forEach(function (cand) {
      var ct = tokens(cand);
      if (latinField) {
        Object.keys(ct).forEach(function (t) { if (!hasAscii(t)) delete ct[t]; });
      }
      var ckeys = Object.keys(ct);
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
    return results.slice(0, limit == null ? 10 : limit);
  }

  // Synchronous version (tests, small inputs). The page uses the worker loop instead.
  function identify(index, values, field, country, limit) {
    var samples = values
      .filter(function (v) { return v != null; })
      .map(function (v) { return String(v).trim(); })
      .filter(Boolean);
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
    tokens: tokens,
    abbreviations: abbreviations,
    identify: identify
  };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.IdentifyCore = api;
})(typeof self !== "undefined" ? self : this);
