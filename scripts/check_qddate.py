#!/usr/bin/env python3
"""Check the registry's qddate mappings against an installed qddate.

qddate (https://github.com/ivbeg/qddate) is not a dependency of the registry,
so this check does not run in CI. Run it after a qddate release:

    pip install qddate
    python scripts/check_qddate.py [data_dir]

It checks that:
- every base date pattern of qddate is mapped by exactly one registry record,
  and no record maps a key that qddate does not have;
- qddate reads every positive example of a mapped record with one of the
  record's keys (a generated variant counts as its base pattern);
- every month name that qddate knows for a language matches the regexp of
  that language's record, in a "<day> <month> <year>" date.

The review of the mappings is devdocs/QDDATE_REVIEW.md.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import qddate
import qddate.patterns as qd_patterns
import yaml
from qddate.patterns.months import MONTHS_BY_LANGUAGE

# qddate language code -> registry record of dates with a month name, and the
# month forms that qddate's patterns of that language use.
LANGUAGE_RECORDS = {
    "en": ("date_english", ("full", "full_lc", "abbrev", "abbrev_lc")),
    "de": ("date_german", ("full", "full_lc", "abbrev", "abbrev_lc")),
    "es": ("date_spanish", ("full", "full_lc", "abbrev", "abbrev_lc")),
    "fr": ("date_french", ("full", "full_lc", "abbrev", "abbrev_lc")),
    "it": ("date_italian", ("full", "full_lc", "abbrev", "abbrev_lc")),
    "nl": ("date_dutch", ("full", "full_lc", "abbrev", "abbrev_lc")),
    "pt": ("date_portuguese", ("full", "full_lc", "abbrev", "abbrev_lc")),
    "ro": ("date_romanian", ("full", "full_lc", "abbrev", "abbrev_lc")),
    "uk": ("date_ukrainian", ("full", "full_lc", "abbrev", "abbrev_lc", "genitive", "genitive_lc")),
    "ru": ("date_russian", ("genitive", "genitive_lc")),
    "bg": ("date_bulgarian", ("full", "full_lc")),
    "tr": ("date_turkish", ("full", "full_lc")),
    "pl": ("date_polish", ("full", "full_lc", "genitive", "genitive_lc")),
    "cz": ("date_czech", ("full", "full_lc", "genitive", "genitive_lc")),
    "sk": ("date_slovak", ("full", "full_lc", "genitive", "genitive_lc")),
}
# qddate's generated variants: a time after or before the date, text after it.
VARIANT = re.compile(r"(?::time_(?:\d+|left))?(?::t_right)?$")


def load_records(data_dir: Path) -> dict[str, dict]:
    records = {}
    for path in sorted((data_dir / "datatypes").rglob("*.yaml")):
        record = yaml.safe_load(path.read_text(encoding="utf-8"))
        if (record.get("mappings") or {}).get("qddate"):
            records[record["id"]] = record
    return records


def keys_of(record: dict) -> list[str]:
    value = record["mappings"]["qddate"]
    return value if isinstance(value, list) else [value]


def main() -> int:
    data_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent.parent / "data"
    records = load_records(data_dir)
    patterns = {p["key"] for p in qd_patterns.ALL_PATTERNS}
    parser = qddate.DateParser()
    errors = []

    owner: dict[str, str] = {}
    for rid, record in records.items():
        for key in keys_of(record):
            if key not in patterns:
                errors.append(f"{rid}: qddate has no pattern {key}")
            if key in owner:
                errors.append(f"{key} is mapped by {owner[key]} and {rid}")
            owner[key] = rid
    for key in sorted(patterns - set(owner)):
        errors.append(f"qddate pattern {key} is not mapped")

    for rid, record in records.items():
        for example in record.get("examples") or []:
            if example.get("valid") is False:
                continue
            found = parser.match(example["value"])
            key = VARIANT.sub("", found["pattern"]["key"], count=1) if found else None
            if key not in keys_of(record):
                errors.append(f"{rid}: qddate reads {example['value']!r} as {key}")

    checked = 0
    for language, (rid, fields) in LANGUAGE_RECORDS.items():
        if rid not in records:
            errors.append(f"no record {rid} for qddate language {language}")
            continue
        regexp = re.compile(records[rid]["regexp"])
        months = MONTHS_BY_LANGUAGE[language]
        for field in fields:
            for name in getattr(months, field) or []:
                checked += 1
                if not regexp.match(f"5 {name} 2022") and not regexp.match(f"5. {name} 2022"):
                    errors.append(f"{rid}: month form {name!r} ({field}) does not match")

    for error in errors:
        print("ERROR", error)
    print(
        f"qddate {getattr(qddate, '__version__', '')}: {len(patterns)} patterns, "
        f"{len(owner)} mapped by {len(records)} records, {checked} month forms, "
        f"{len(errors)} error(s)"
    )
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
