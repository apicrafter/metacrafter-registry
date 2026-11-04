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


def gtin(value: str) -> bool:
    """GS1 mod 10 for GTIN-8, GTIN-12 (UPC), GTIN-13 (EAN) and GTIN-14."""
    digits = _digits(value)
    if not digits or len(digits) not in (8, 12, 13, 14):
        return False
    body, check = digits[:-1], digits[-1]
    total = sum(d * (3 if i % 2 == 0 else 1) for i, d in enumerate(reversed(body)))
    return (10 - total % 10) % 10 == check


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


ALGORITHMS: dict[str, Callable[[str], bool]] = {
    "luhn": luhn,
    "iban_mod97": iban_mod97,
    "gtin": gtin,
    "isbn10": isbn10,
    "isbn13": isbn13,
    "ru_inn": ru_inn,
    "ru_snils": ru_snils,
    "ru_ogrn": ru_ogrn,
    "fr_nir": fr_nir,
    "at_uid": at_uid,
    "bg_vat": bg_vat,
}


def check(algorithm: str, value: str) -> bool:
    """Run a named algorithm; raises KeyError for an unknown name."""
    return ALGORITHMS[algorithm](value)
