"""Normalized registry model used by the site and the ``/api/v1/`` emitters.

Unlike the legacy shape, references are plain id strings (resolved through the
reference lists), empty values are omitted, booleans are booleans and
translations always have the ``{name, doc}`` shape.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .loader import RegistrySources
from .quality import score_record

REPO_URL = "https://github.com/apicrafter/metacrafter-registry"
EDIT_URL = REPO_URL + "/edit/main/data/{path}"
SOURCE_URL = REPO_URL + "/blob/main/data/{path}"


def _as_bool(value: Any) -> bool:
    return value is True or str(value) == "True"


def _ids(values: Any) -> list[str]:
    return [str(v).strip() for v in values or [] if str(v).strip()]


def _present(value: Any) -> bool:
    return value not in (None, "", [], {})


def _translations(raw: Any) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    for lang, value in (raw or {}).items():
        if isinstance(value, str):
            entry = {"name": value} if value.strip() else {}
        elif isinstance(value, dict):
            entry = {k: str(v) for k, v in value.items() if k in ("name", "doc") and _present(v)}
        else:
            entry = {}
        if entry:
            out[str(lang)] = entry
    return out


def _examples(raw: Any) -> list[dict[str, Any]]:
    out = []
    for example in raw or []:
        if not isinstance(example, dict) or not _present(example.get("value")):
            continue
        item: dict[str, Any] = {"value": str(example["value"])}
        if _present(example.get("description")):
            item["description"] = str(example["description"]).strip()
        item["valid"] = example.get("valid", True) is not False
        out.append(item)
    return out


def _links(raw: Any) -> list[dict[str, str]]:
    out = []
    for link in raw or []:
        if isinstance(link, dict) and _present(link.get("url")):
            out.append({"type": str(link.get("type") or "other"), "url": str(link["url"])})
    return out


@dataclass
class Registry:
    """Normalized datatypes, tools and reference lists, all keyed and sorted by id."""

    datatypes: dict[str, dict[str, Any]]
    tools: dict[str, dict[str, Any]]
    categories: dict[str, dict[str, Any]]
    countries: dict[str, dict[str, Any]]
    langs: dict[str, dict[str, Any]]
    tools_by_type: dict[str, list[str]] = field(default_factory=dict)
    aliases: dict[str, str] = field(default_factory=dict)  # alias -> canonical id

    def kind_count(self, kind: str) -> int:
        return sum(1 for r in self.datatypes.values() if r["kind"] == kind)


def build_registry(sources: RegistrySources, site_url: str) -> Registry:
    site_url = site_url.rstrip("/")
    raw = {rec.id: rec for rec in sources.datatypes}

    patterns_of: dict[str, list[str]] = {}
    children_of: dict[str, list[str]] = {}
    for rid in sorted(raw):
        data = raw[rid].data
        if _present(data.get("semantic_type")):
            patterns_of.setdefault(str(data["semantic_type"]), []).append(rid)
        parent = data.get("parent")
        parent_id = parent.get("type") if isinstance(parent, dict) else parent
        if _present(parent_id):
            children_of.setdefault(str(parent_id), []).append(rid)

    tools_by_type: dict[str, list[str]] = {}
    for rec in sorted(sources.tools, key=lambda r: r.id):
        for supported in _ids(rec.data.get("supported_types")):
            tools_by_type.setdefault(supported, []).append(rec.id)

    datatypes: dict[str, dict[str, Any]] = {}
    for rid in sorted(raw):
        rec = raw[rid]
        data = rec.data
        semantic_type = str(data["semantic_type"]) if _present(data.get("semantic_type")) else None
        parent_rec = raw.get(semantic_type).data if semantic_type in raw else {}
        parent = data.get("parent")
        parent_id = parent.get("type") if isinstance(parent, dict) else parent

        record: dict[str, Any] = {
            "id": rid,
            "kind": "pattern" if semantic_type else "datatype",
            "status": str(data.get("status") or "stable"),
            "name": str(data.get("name", "")).strip(),
            "doc": str(data.get("doc", "")).strip(),
        }
        if semantic_type:
            record["semantic_type"] = semantic_type
        if _present(parent_id):
            record["parent"] = str(parent_id)
        for key in ("aliases",):
            values = _ids(data.get(key))
            if values:
                record[key] = values
        if _present(data.get("replaced_by")):
            record["replaced_by"] = str(data["replaced_by"])
        if rid in children_of:
            record["children"] = children_of[rid]
        if rid in patterns_of:
            record["patterns"] = patterns_of[rid]
        # A pattern inherits is_pii, categories and classification unless it declares them.
        record["is_pii"] = _as_bool(
            data["is_pii"] if "is_pii" in data else parent_rec.get("is_pii")
        )
        for key in ("categories", "country", "langs"):
            values = _ids(data.get(key))
            if not values and key == "categories" and semantic_type:
                values = _ids(parent_rec.get(key))
            if values:
                record[key] = values
        classification = data.get("classification") or parent_rec.get("classification")
        if _present(classification):
            record["classification"] = str(classification)
        if _present(data.get("regexp")):
            record["regexp"] = str(data["regexp"])
        if _present(data.get("checksum")):
            record["checksum"] = str(data["checksum"])
        examples = _examples(data.get("examples"))
        if examples:
            record["examples"] = examples
        mappings = {k: v for k, v in (data.get("mappings") or {}).items() if _present(v)}
        if _present(data.get("wikidata_property")):  # v1 sources
            mappings.setdefault("wikidata", str(data["wikidata_property"]).strip())
        if mappings:
            record["mappings"] = dict(sorted(mappings.items()))
        links = _links(data.get("links"))
        if links:
            record["links"] = links
        translations = _translations(data.get("translations"))
        if translations:
            record["translations"] = translations
        if rid in tools_by_type:
            record["detected_by"] = {"tools": tools_by_type[rid]}
        record["quality"] = score_record(record)
        record["source"] = {
            "path": "data/" + rec.relpath,
            "url": SOURCE_URL.format(path=rec.relpath),
            "edit_url": EDIT_URL.format(path=rec.relpath),
        }
        record["urls"] = {
            "html": f"{site_url}/datatype/{rid}",
            "json": f"{site_url}/api/v1/datatypes/{rid}.json",
        }
        datatypes[rid] = record

    tools: dict[str, dict[str, Any]] = {}
    for rec in sorted(sources.tools, key=lambda r: r.id):
        data = rec.data
        tool: dict[str, Any] = {
            "id": rec.id,
            "name": str(data.get("name", "")).strip(),
            "category": str(data.get("category", "")),
            "doc": str(data.get("doc", "")).strip(),
        }
        if _present(data.get("website")):
            tool["website"] = str(data["website"])
        tool["supported_types"] = _ids(data.get("supported_types"))
        tool["source"] = {
            "path": "data/" + rec.relpath,
            "url": SOURCE_URL.format(path=rec.relpath),
            "edit_url": EDIT_URL.format(path=rec.relpath),
        }
        tool["urls"] = {
            "html": f"{site_url}/tool/{rec.id}",
            "json": f"{site_url}/api/v1/tools/{rec.id}.json",
        }
        tools[rec.id] = tool

    def reference(entries: dict[str, dict[str, Any]], field_name: str, path: str):
        counts: dict[str, int] = {}
        for record in datatypes.values():
            for value in record.get(field_name, []):
                counts[value] = counts.get(value, 0) + 1
        out = {}
        for key in sorted(entries):
            entry = {"id": key, "name": str(entries[key]["name"]).strip()}
            if entries[key].get("kind"):
                entry["kind"] = str(entries[key]["kind"])
            entry["count"] = counts.get(key, 0)
            if path:
                entry["url"] = f"{site_url}/{path}/{key}"
            out[key] = entry
        return out

    return Registry(
        datatypes=datatypes,
        tools=tools,
        categories=reference(sources.categories, "categories", "category"),
        countries=reference(sources.countries, "country", "country"),
        langs=reference(sources.langs, "langs", ""),
        tools_by_type=tools_by_type,
        aliases=dict(
            sorted((alias, rid) for rid, r in datatypes.items() for alias in r.get("aliases", []))
        ),
    )


CSV_COLUMNS = [
    "id",
    "kind",
    "name",
    "doc",
    "semantic_type",
    "parent",
    "categories",
    "country",
    "langs",
    "is_pii",
    "classification",
    "regexp",
    "wikidata",
    "url",
    "status",
    "quality_score",
    "aliases",
]


def csv_row(record: dict[str, Any]) -> list[str]:
    def joined(key: str) -> str:
        return "|".join(record.get(key, []))

    return [
        record["id"],
        record["kind"],
        record["name"],
        record["doc"],
        record.get("semantic_type", ""),
        record.get("parent", ""),
        joined("categories"),
        joined("country"),
        joined("langs"),
        "true" if record["is_pii"] else "false",
        record.get("classification", ""),
        record.get("regexp", ""),
        record.get("mappings", {}).get("wikidata", ""),
        record["urls"]["html"],
        record["status"],
        str(record["quality"]["score"]),
        joined("aliases"),
    ]
