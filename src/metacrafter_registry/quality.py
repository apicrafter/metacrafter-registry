"""Quality score of a record: 0-100, with the list of missing elements.

Rubric (design.md D7). Each element gives up to its points:

=================================  ======  =====================================
Element                            Points  Partial credit
=================================  ======  =====================================
Description                        20      10 if 25-59 characters
Regular expression                 20      10 if not anchored with ^...$
Positive examples (2 or more)      15      8 for a single example
Negative example                   5
Source link                        15      8 if only links of type 'other'
Mapping (e.g. Wikidata)            10
Translation                        5
Detector coverage                  10      a metacrafter rule or a tool record
=================================  ======  =====================================
"""

from __future__ import annotations

from typing import Any

AUTHORITATIVE_LINKS = {
    "wikipedia",
    "wikidata",
    "schema.org",
    "doc",
    "dublincore",
    "bioschemas",
    "datadrivendiscovery",
}


def score_record(record: dict[str, Any]) -> dict[str, Any]:
    """Score a normalized (``/api/v1/``) record; return {'score': int, 'missing': [str]}."""
    score = 0
    missing: list[str] = []

    doc = record.get("doc", "")
    if doc.strip().lower() == record.get("name", "").strip().lower() or len(doc) < 25:
        missing.append("description")
    elif len(doc) < 60:
        score += 10
        missing.append("longer description")
    else:
        score += 20

    regexp = record.get("regexp")
    if not regexp:
        missing.append("regexp")
    elif regexp.startswith("^") and regexp.endswith("$"):
        score += 20
    else:
        score += 10
        missing.append("anchored regexp")

    examples = record.get("examples", [])
    positive = [e for e in examples if e.get("valid", True)]
    if len(positive) >= 2:
        score += 15
    elif len(positive) == 1:
        score += 8
        missing.append("second example")
    else:
        missing.append("examples")
    if any(not e.get("valid", True) for e in examples):
        score += 5
    else:
        missing.append("negative example")

    links = record.get("links", [])
    if any(link["type"] in AUTHORITATIVE_LINKS for link in links):
        score += 15
    elif links:
        score += 8
        missing.append("authoritative source link")
    else:
        missing.append("source link")

    if record.get("mappings"):
        score += 10
    else:
        missing.append("mapping (Wikidata, Schema.org, ...)")

    if record.get("translations"):
        score += 5
    else:
        missing.append("translation")

    detected_by = record.get("detected_by", {})
    if detected_by.get("metacrafter_rules") or detected_by.get("tools"):
        score += 10
    else:
        missing.append("detector coverage")

    return {"score": score, "missing": missing}
