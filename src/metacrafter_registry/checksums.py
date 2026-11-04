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


ALGORITHMS: dict[str, Callable[[str], bool]] = {
    "luhn": luhn,
    "iban_mod97": iban_mod97,
    "gtin": gtin,
    "isbn10": isbn10,
    "isbn13": isbn13,
    "ru_inn": ru_inn,
    "ru_snils": ru_snils,
    "ru_ogrn": ru_ogrn,
}


def check(algorithm: str, value: str) -> bool:
    """Run a named algorithm; raises KeyError for an unknown name."""
    return ALGORITHMS[algorithm](value)
