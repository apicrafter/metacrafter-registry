"""Check-digit algorithms referenced by the ``checksum`` field of records.

Each function takes the raw value and returns True when the check digit is
valid. Separators (spaces, hyphens, dots) are ignored; any other unexpected
character makes the value invalid.
"""

from __future__ import annotations

import re
from collections.abc import Callable

_SEPARATORS = re.compile(r"[\s\-.]")


def _compact(value: str) -> str:
    return _SEPARATORS.sub("", str(value))


def _digits(value: str) -> list[int] | None:
    compact = _compact(value)
    return [int(c) for c in compact] if compact.isdigit() else None


def luhn(value: str) -> bool:
    """Luhn (mod 10): payment card numbers, IMEI."""
    digits = _digits(value)
    if not digits or len(digits) < 2:
        return False
    total = 0
    for i, d in enumerate(reversed(digits)):
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def iban_mod97(value: str) -> bool:
    """ISO 13616 IBAN: move the first four characters to the end, mod 97 == 1."""
    compact = _compact(value).upper()
    if not re.fullmatch(r"[A-Z]{2}\d{2}[A-Z0-9]{11,30}", compact):
        return False
    rearranged = compact[4:] + compact[:4]
    return int("".join(str(int(c, 36)) for c in rearranged)) % 97 == 1


def gs1_mod10(value: str) -> bool:
    """GS1 standard check digit of a numeric key of any length.

    Weights 3 and 1 alternate from the right, starting with 3 next to the
    check digit. Used by GLN (13 digits), GSIN (17), GSRN and SSCC (18).
    Leading zeros do not change the result, so an SSCC written with its
    Application Identifier (00) passes too.
    """
    digits = _digits(value)
    if not digits or len(digits) < 2:
        return False
    body, check = digits[:-1], digits[-1]
    total = sum(d * (3 if i % 2 == 0 else 1) for i, d in enumerate(reversed(body)))
    return (10 - total % 10) % 10 == check


def gtin(value: str) -> bool:
    """GS1 mod 10 for GTIN-8, GTIN-12 (UPC), GTIN-13 (EAN) and GTIN-14."""
    digits = _digits(value)
    if not digits or len(digits) not in (8, 12, 13, 14):
        return False
    return gs1_mod10(value)


# GS1 character sets of the General Specifications, in weight order.
_GS1_CSET82 = "!\"%&'()*+,-./0123456789:;<=>?ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqrstuvwxyz"
_GS1_CSET32 = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"


def _primes(count: int) -> list[int]:
    primes: list[int] = []
    candidate = 2
    while len(primes) < count:
        if all(candidate % p for p in primes if p * p <= candidate):
            primes.append(candidate)
        candidate += 1
    return primes


def gs1_checkpair(value: str) -> bool:
    """GS1 check character pair: Global Model Number (GMN) and HIDRI.

    Each character before the pair has its position in CSET 82 as its value.
    The values are weighted by the primes 2, 3, 5, ... from the right and
    summed modulo 1021; the two 5-bit halves of the sum, looked up in CSET 32,
    are the check characters. Hyphens and dots are data here, not separators.
    """
    data = str(value).strip()
    if len(data) < 2:
        return False
    body, pair = data[:-2], data[-2:]
    if any(c not in _GS1_CSET82 for c in body):
        return False
    weights = _primes(len(body))
    total = (
        sum(_GS1_CSET82.index(c) * w for c, w in zip(reversed(body), weights, strict=True)) % 1021
    )
    return pair == _GS1_CSET32[total >> 5] + _GS1_CSET32[total & 31]


def isbn13(value: str) -> bool:
    digits = _digits(value)
    return bool(digits) and len(digits) == 13 and gtin(value)


def isbn10(value: str) -> bool:
    compact = _compact(value).upper()
    if not re.fullmatch(r"\d{9}[\dX]", compact):
        return False
    numbers = [10 if c == "X" else int(c) for c in compact]
    return sum(w * d for w, d in zip(range(10, 0, -1), numbers, strict=True)) % 11 == 0


def ru_inn(value: str) -> bool:
    """Russian taxpayer number: 10 digits (organizations) or 12 (individuals)."""
    digits = _digits(value)
    if not digits:
        return False

    def check(weights: list[int]) -> int:
        return sum(w * d for w, d in zip(weights, digits, strict=False)) % 11 % 10

    if len(digits) == 10:
        return check([2, 4, 10, 3, 5, 9, 4, 6, 8]) == digits[9]
    if len(digits) == 12:
        return (
            check([7, 2, 4, 10, 3, 5, 9, 4, 6, 8]) == digits[10]
            and check([3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8]) == digits[11]
        )
    return False


def ru_snils(value: str) -> bool:
    """Russian insurance number (SNILS): 9 digits and a 2-digit control number."""
    digits = _digits(value)
    if not digits or len(digits) != 11:
        return False
    total = sum(d * (9 - i) for i, d in enumerate(digits[:9]))
    if total > 101:
        total %= 101
    control = 0 if total in (100, 101) else total
    return control == digits[9] * 10 + digits[10]


def ru_ogrn(value: str) -> bool:
    """Russian state registration number: OGRN (13 digits) or OGRNIP (15 digits)."""
    compact = _compact(value)
    if not compact.isdigit():
        return False
    if len(compact) == 13:
        return int(compact[:12]) % 11 % 10 == int(compact[12])
    if len(compact) == 15:
        return int(compact[:14]) % 13 % 10 == int(compact[14])
    return False


def fr_nir(value: str) -> bool:
    """French social security number (NIR): 13 characters and a 2-digit key.

    The key is 97 minus the 13-character number modulo 97; the Corsican
    department codes 2A and 2B count as 19 and 18.
    """
    compact = _compact(value).upper()
    if not re.fullmatch(r"\d{5}(?:\d{2}|2[AB])\d{8}", compact):
        return False
    department = {"2A": "19", "2B": "18"}.get(compact[5:7], compact[5:7])
    body = int(compact[:5] + department + compact[7:13])
    return 97 - body % 97 == int(compact[13:])


def at_uid(value: str) -> bool:
    """Austrian VAT number (UID): U and 8 digits, optionally prefixed with AT.

    The check digit is (6 - Luhn sum of the 7 digits before it) mod 10.
    """
    compact = _compact(value).upper()
    if compact.startswith("AT"):
        compact = compact[2:]
    if not re.fullmatch(r"U\d{8}", compact):
        return False
    digits = [int(c) for c in compact[1:]]
    total = 0
    for i, d in enumerate(reversed(digits[:-1])):
        total += d if i % 2 == 0 else sum(divmod(d * 2, 10))
    return (6 - total) % 10 == digits[-1]


def bg_vat(value: str) -> bool:
    """Bulgarian VAT number: 9 digits (legal entities) or 10 digits, optionally prefixed with BG.

    A 10-digit number passes when its last digit matches the EGN, the PNF or
    the generic check digit; the birth date inside an EGN is not checked.
    """
    compact = _compact(value).upper()
    if compact.startswith("BG"):
        compact = compact[2:]
    digits = [int(c) for c in compact] if compact.isdigit() else None
    if not digits:
        return False

    def weighted(weights: tuple[int, ...]) -> int:
        return sum(w * d for w, d in zip(weights, digits, strict=False))

    if len(digits) == 9:
        check = weighted((1, 2, 3, 4, 5, 6, 7, 8)) % 11
        if check == 10:
            check = weighted((3, 4, 5, 6, 7, 8, 9, 10)) % 11
        return check % 10 == digits[8]
    if len(digits) == 10:
        egn = weighted((2, 4, 8, 5, 10, 9, 7, 3, 6)) % 11 % 10
        pnf = weighted((21, 19, 17, 13, 11, 9, 7, 3, 1)) % 10
        other = (11 - weighted((4, 3, 2, 7, 6, 5, 4, 3, 2))) % 11
        return digits[9] in (egn, pnf, other)
    return False


def no_fnr(value: str) -> bool:
    """Norwegian national identity number (fødselsnummer, D-number): 11 digits.

    The last two digits are mod-11 check digits; the second one covers the
    first. A check digit that would be 10 makes the number invalid.
    """
    digits = _digits(value)
    if not digits or len(digits) != 11:
        return False

    def check(weights: tuple[int, ...]) -> int:
        return (11 - sum(w * d for w, d in zip(weights, digits, strict=False))) % 11

    return (
        check((3, 7, 6, 1, 8, 9, 4, 5, 2)) == digits[9]
        and check((5, 4, 3, 2, 7, 6, 5, 4, 3, 2)) == digits[10]
    )


_CF_CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
# Values of A-Z in odd positions; the digits 0-9 take the values of A-J.
# fmt: off
_CF_ODD_LETTERS = (
    1, 0, 5, 7, 9, 13, 15, 17, 19, 21, 2, 4, 18, 20, 11, 3, 6, 8, 12, 14, 16, 10, 22, 25, 24, 23,
)
# fmt: on
_CF_ODD = {c: _CF_ODD_LETTERS[i if i < 10 else i - 10] for i, c in enumerate(_CF_CHARS)}
_CF_EVEN = {c: i if i < 10 else i - 10 for i, c in enumerate(_CF_CHARS)}


def it_codicefiscale(value: str) -> bool:
    """Italian fiscal code of a person: 16 characters, the last one a check letter.

    Characters in odd positions (1st, 3rd, ...) and even positions have
    separate value tables; the check letter is the sum modulo 26 (A = 0).
    Letters that replace digits on clashes (omocodia) are accepted.
    """
    compact = _compact(value).upper()
    if not re.fullmatch(
        r"[A-Z]{6}[0-9LMNP-V]{2}[ABCDEHLMPRST][0-9LMNP-V]{2}[A-Z][0-9LMNP-V]{3}[A-Z]", compact
    ):
        return False
    total = sum(_CF_ODD[c] if i % 2 == 0 else _CF_EVEN[c] for i, c in enumerate(compact[:15]))
    return chr(ord("A") + total % 26) == compact[15]


def it_iva(value: str) -> bool:
    """Italian VAT number (partita IVA): 11 digits, optionally prefixed with IT.

    Digits 8-10 are the tax office code (001-100, 120, 121, 888 or 999) and
    the last digit is a Luhn check digit.
    """
    compact = _compact(value).upper()
    if compact.startswith("IT"):
        compact = compact[2:]
    if not re.fullmatch(r"\d{11}", compact) or int(compact[:7]) == 0:
        return False
    office = compact[7:10]
    if not ("001" <= office <= "100" or office in ("120", "121", "888", "999")):
        return False
    return luhn(compact)


def fi_hetu(value: str) -> bool:
    """Finnish personal identity code (henkilötunnus): 11 characters, DDMMYYCZZZQ.

    The control character is the 9-digit number DDMMYYZZZ modulo 31 looked up
    in 0123456789ABCDEFHJKLMNPRSTUVWXY. The hyphen is a century sign, so it is
    not stripped; the birth date is not checked.
    """
    compact = re.sub(r"\s", "", str(value)).upper()
    match = re.fullmatch(r"(\d{6})[-+A-FU-Y](\d{3})([0-9A-FHJ-NPR-Y])", compact)
    if not match:
        return False
    return "0123456789ABCDEFHJKLMNPRSTUVWXY"[int(match[1] + match[2]) % 31] == match[3]


def es_dni(value: str) -> bool:
    """Spanish DNI: 8 digits and a check letter, the number modulo 23 in TRWAGMYFPDXBNJZSQVHLCKE."""
    compact = _compact(value).upper()
    if not re.fullmatch(r"\d{8}[A-Z]", compact):
        return False
    return "TRWAGMYFPDXBNJZSQVHLCKE"[int(compact[:8]) % 23] == compact[8]


def _strip_prefix(value: str, prefix: str) -> str:
    compact = _compact(value).upper()
    return compact[len(prefix) :] if compact.startswith(prefix) else compact


def pl_nip(value: str) -> bool:
    """Polish tax number (NIP): 10 digits, optionally prefixed with PL.

    The last digit is the sum of the first nine digits weighted 6 5 7 2 3 4 5
    6 7, modulo 11. A sum that gives 10 makes the number invalid.
    """
    compact = _strip_prefix(value, "PL")
    if not re.fullmatch(r"\d{10}", compact):
        return False
    digits = [int(c) for c in compact]
    weights = (6, 5, 7, 2, 3, 4, 5, 6, 7)
    return sum(w * d for w, d in zip(weights, digits, strict=False)) % 11 == digits[9]


def sk_dph(value: str) -> bool:
    """Slovak VAT number (IČ DPH): 10 digits, optionally prefixed with SK.

    The first digit is not 0 and the whole number is divisible by 11.
    """
    compact = _strip_prefix(value, "SK")
    return bool(re.fullmatch(r"[1-9]\d{9}", compact)) and int(compact) % 11 == 0


def si_ddv(value: str) -> bool:
    """Slovenian VAT number (ID za DDV): 8 digits, optionally prefixed with SI.

    The first digit is not 0. The check digit is 11 minus the sum of the first
    seven digits weighted 8 down to 2, modulo 11; a result of 10 gives 0 and a
    result of 11 makes the number invalid.
    """
    compact = _strip_prefix(value, "SI")
    if not re.fullmatch(r"[1-9]\d{7}", compact):
        return False
    digits = [int(c) for c in compact]
    check = 11 - sum((8 - i) * d for i, d in enumerate(digits[:7])) % 11
    return check != 11 and check % 10 == digits[7]


def se_vat(value: str) -> bool:
    """Swedish VAT number (momsregistreringsnummer): 12 digits, optionally prefixed with SE.

    The first ten digits are the organisation or personal number with a Luhn
    check digit, and the last two are 01.
    """
    compact = _strip_prefix(value, "SE")
    return bool(re.fullmatch(r"\d{10}01", compact)) and luhn(compact[:10])


def kz_iin_bin(value: str) -> bool:
    """Kazakh individual (IIN) or business (BIN) identification number: 12 digits.

    The 12th digit is the sum of the first eleven digits weighted 1 to 11,
    modulo 11. When that gives 10, the weights 3 4 5 6 7 8 9 10 11 1 2 are
    used instead; a second 10 means the number is never issued.
    """
    digits = _digits(value)
    if not digits or len(digits) != 12:
        return False
    check = sum(w * d for w, d in zip(range(1, 12), digits, strict=False)) % 11
    if check == 10:
        weights = (3, 4, 5, 6, 7, 8, 9, 10, 11, 1, 2)
        check = sum(w * d for w, d in zip(weights, digits, strict=False)) % 11
    return check != 10 and check == digits[11]


ALGORITHMS: dict[str, Callable[[str], bool]] = {
    "luhn": luhn,
    "iban_mod97": iban_mod97,
    "gtin": gtin,
    "gs1_mod10": gs1_mod10,
    "gs1_checkpair": gs1_checkpair,
    "isbn10": isbn10,
    "isbn13": isbn13,
    "ru_inn": ru_inn,
    "ru_snils": ru_snils,
    "ru_ogrn": ru_ogrn,
    "fr_nir": fr_nir,
    "at_uid": at_uid,
    "bg_vat": bg_vat,
    "no_fnr": no_fnr,
    "it_codicefiscale": it_codicefiscale,
    "it_iva": it_iva,
    "fi_hetu": fi_hetu,
    "es_dni": es_dni,
    "pl_nip": pl_nip,
    "sk_dph": sk_dph,
    "si_ddv": si_ddv,
    "se_vat": se_vat,
    "kz_iin_bin": kz_iin_bin,
}


def check(algorithm: str, value: str) -> bool:
    """Run a named algorithm; raises KeyError for an unknown name."""
    return ALGORITHMS[algorithm](value)
