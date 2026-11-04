"""Legacy (release 1.02) JSON shape.

This shape is a public contract: ``/registry.json``, ``/datatype/<id>.json``,
``/tools.json``, ``/tool/<id>.json`` and the committed ``data/*_latest.*`` files
are consumed by metacrafter's ``RegistryClient``, metacrafter LLM mode and
``ecosystem_check.py``. Fields may be added, never removed or retyped.

Differences from the old ``scripts/builder.py`` output (bug fixes, not shape
changes):

* records are ordered by id, so output is deterministic;
* patterns embedded in a datatype are always fully resolved (the old JSONL
  sometimes embedded raw, unresolved pattern objects);
* a pattern's ``is_pii`` always reflects its parent datatype (the old builder
  compared against an already-converted boolean, depending on file order).
"""

from __future__ import annotations

import copy
import logging
from typing import Any

from .loader import RegistrySources

logger = logging.getLogger(__name__)


def _as_bool(value: Any) -> bool:
    return value is True or str(value) == "True"


def _resolve(ids: list[Any], reference: dict[str, dict[str, Any]]) -> list[dict[str, str]]:
    out = []
    for raw in ids or []:
        key = str(raw).strip()
        entry = reference.get(key)
        if entry is None:
            logger.warning("Unknown reference '%s', skipping", key)
            continue
        out.append({"id": key, "name": entry["name"]})
    return out


def build_datatypes(sources: RegistrySources) -> dict[str, dict[str, Any]]:
    """Return legacy-shaped datatypes and patterns keyed by id, sorted by id."""
    raw = {rec.id: rec.data for rec in sources.datatypes}
    patterns_of: dict[str, list[str]] = {}
    for rid in sorted(raw):
        record = raw[rid]
        if "semantic_type" in record:
            patterns_of.setdefault(str(record["semantic_type"]), []).append(rid)

    processed: dict[str, dict[str, Any]] = {}
    for rid in sorted(raw):
        record = copy.deepcopy(raw[rid])
        record.pop("patterns", None)  # derived below
        if "semantic_type" in record:
            parent = raw.get(str(record["semantic_type"]), {})
            record["type"] = "pattern"
            # v2: a pattern inherits what it does not declare
            record["is_pii"] = _as_bool(record.get("is_pii", parent.get("is_pii")))
            if "categories" not in record and parent.get("categories"):
                record["categories"] = list(parent["categories"])
            if "classification" not in record and "classification" in parent:
                record["classification"] = parent["classification"]
        else:
            record["type"] = "datatype"
            record["is_pii"] = _as_bool(record.get("is_pii"))
        if isinstance(record.get("parent"), str):  # v2 id string -> legacy {type: id}
            record["parent"] = {"type": record["parent"]}
        wikidata = (record.get("mappings") or {}).get("wikidata")
        if wikidata and "wikidata_property" not in record:
            record["wikidata_property"] = wikidata
        for key, default in (
            ("categories", []),
            ("links", []),
            ("examples", []),
            ("translations", {}),
        ):
            record.setdefault(key, default)  # present on every 1.02 record
        record["categories"] = _resolve(record["categories"], sources.categories)
        if "country" in record:
            record["country"] = _resolve(record["country"], sources.countries)
        if "langs" in record:
            record["langs"] = _resolve(record["langs"], sources.langs)
        processed[rid] = record

    for rid, record in processed.items():
        if rid in patterns_of:
            record["patterns"] = [copy.deepcopy(processed[pid]) for pid in patterns_of[rid]]

    # Retired IDs keep resolving: an alias entry is the canonical record under the old id.
    aliases: dict[str, dict[str, Any]] = {}
    for rid, record in processed.items():
        for alias in raw[rid].get("aliases") or []:
            aliases[str(alias)] = {**copy.deepcopy(record), "id": str(alias), "alias_of": rid}
    processed.update(aliases)
    return dict(sorted(processed.items()))


def build_tools(sources: RegistrySources) -> dict[str, dict[str, Any]]:
    """Return legacy-shaped tools keyed by id, sorted by id."""
    tools = {}
    for rec in sorted(sources.tools, key=lambda r: r.id):
        record = copy.deepcopy(rec.data)
        record["num"] = len(record.get("supported_types") or [])
        tools[rec.id] = record
    return tools
