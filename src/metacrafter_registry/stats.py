"""Honest completeness statistics and per-record quality report.

A field counts as present only when it has a non-empty value.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from .model import Registry

FIELDS = [
    ("regexp", "regexp"),
    ("examples", "examples"),
    ("links", "source links"),
    ("mappings", "mappings (Wikidata, ...)"),
    ("translations", "translations"),
    ("classification", "classification"),
    ("detected_by", "supported by a tool"),
]


def _pct(part: int, whole: int) -> str:
    return f"{part * 100.0 / whole:5.1f}%" if whole else "  n/a"


def stats_lines(reg: Registry) -> list[str]:
    records = list(reg.datatypes.values())
    total = len(records)
    lines = [
        f"Datatypes: {reg.kind_count('datatype')}",
        f"Patterns:  {reg.kind_count('pattern')}",
        f"Tools:     {len(reg.tools)}",
        f"Aliases:   {len(reg.aliases)}",
        "",
        "Status:",
    ]
    for status, count in sorted(Counter(r["status"] for r in records).items()):
        lines.append(f"  {status:<11} {count:4d}  {_pct(count, total)}")
    lines += ["", "Completeness (non-empty values only):"]
    for key, label in FIELDS:
        count = sum(1 for r in records if r.get(key))
        lines.append(f"  {label:<26} {count:4d}  {_pct(count, total)}")
    anchored = sum(
        1 for r in records if r.get("regexp", "").startswith("^") and r["regexp"].endswith("$")
    )
    lines.append(f"  {'anchored regexp':<26} {anchored:4d}  {_pct(anchored, total)}")

    scores = [r["quality"]["score"] for r in records]
    lines += ["", f"Quality score: average {sum(scores) / total:.1f}" if total else ""]
    for low, high in ((0, 25), (25, 50), (50, 75), (75, 90), (90, 101)):
        count = sum(1 for s in scores if low <= s < high)
        label = f"{low}-{min(high, 100)}"
        lines.append(
            f"  {label:<8} {count:4d}  {_pct(count, total)}  {'#' * (count * 50 // max(total, 1))}"
        )

    missing = Counter(m for r in records for m in r["quality"]["missing"])
    lines += ["", "Most common missing elements:"]
    for element, count in missing.most_common():
        lines.append(f"  {element:<36} {count:4d}  {_pct(count, total)}")

    by_country: Counter[str] = Counter()
    for r in records:
        for c in r.get("country") or ["(global)"]:
            by_country[c] += 1
    lines += ["", "Records by country:"]
    for country, count in by_country.most_common():
        lines.append(f"  {country:<9} {count:4d}")
    return lines


def report_rows(
    reg: Registry, status: str | None = None, below: int | None = None
) -> list[dict[str, Any]]:
    rows = []
    for r in reg.datatypes.values():
        if status and r["status"] != status:
            continue
        if below is not None and r["quality"]["score"] >= below:
            continue
        rows.append(
            {
                "id": r["id"],
                "status": r["status"],
                "score": r["quality"]["score"],
                "missing": r["quality"]["missing"],
                "path": r["source"]["path"],
            }
        )
    return sorted(rows, key=lambda row: (row["score"], row["id"]))
