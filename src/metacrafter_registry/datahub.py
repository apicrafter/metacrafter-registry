"""DataHub business glossary export (``/datahub-glossary.yml``).

The file is a DataHub business glossary (the ``datahub.business_glossary``
ingestion source, format version 1). Each registry record becomes one glossary
term whose ``id`` is the registry id, so its URN is
``urn:li:glossaryTerm:<id>``: the URN that ``metacrafter export datahub``
attaches to the columns it detects.

Terms are grouped under one ``Metacrafter Registry`` node, with a child node
per category; a record is placed in the node of its first category. A record
mapped to FIBO cites the FIBO class as its source (``source_ref: FIBO``,
``source_url`` = the class IRI); other records cite their registry page.
Patterns and subtypes inherit (``IsA``) their datatype and parent.
"""

from __future__ import annotations

from typing import Any

import yaml

from .fibo import fibo_iris
from .model import RegistryModel

ROOT_ID = "metacrafter-registry"
ROOT_NAME = "Metacrafter Registry"
DEFAULT_OWNER = "datahub"


def _term_names(records: list[dict[str, Any]]) -> dict[str, str]:
    """Term names that are unique within their node: the record name, plus the id on a clash."""
    seen: dict[tuple[str, str], int] = {}
    for record in records:
        key = (record["categories"][0], record["name"] or record["id"])
        seen[key] = seen.get(key, 0) + 1
    names = {}
    for record in records:
        name = record["name"] or record["id"]
        if seen[(record["categories"][0], name)] > 1:
            name = f"{name} ({record['id']})"
        names[record["id"]] = name
    return names


def _custom_properties(record: dict[str, Any], iris: list[str]) -> dict[str, str]:
    """String-valued properties: DataHub stores custom properties as strings."""
    props = {
        "registry_id": record["id"],
        "kind": record["kind"],
        "status": record["status"],
        "is_pii": "true" if record["is_pii"] else "false",
    }
    if record.get("classification"):
        props["classification"] = record["classification"]
    plural = (("categories", "categories"), ("country", "countries"), ("langs", "languages"))
    for key, prop in plural:
        if record.get(key):
            props[prop] = ",".join(record[key])
    for key in ("regexp", "checksum", "replaced_by"):
        if record.get(key):
            props[key] = record[key]
    if record.get("aliases"):
        props["aliases"] = ",".join(record["aliases"])
    wikidata = record.get("mappings", {}).get("wikidata")
    if isinstance(wikidata, str):
        props["wikidata"] = wikidata
    if iris:
        props["fibo"] = " ".join(iris)
    props["registry_url"] = record["urls"]["html"]
    return props


def _knowledge_links(record: dict[str, Any]) -> list[dict[str, str]]:
    links = [{"label": ROOT_NAME, "url": record["urls"]["html"]}]
    seen = {record["urls"]["html"]}
    for link in record.get("links", []):
        if link["url"] not in seen:
            seen.add(link["url"])
            links.append({"label": link["type"], "url": link["url"]})
    return links


def business_glossary(reg: RegistryModel, site_url: str) -> dict[str, Any]:
    """Build the glossary document from normalized records."""
    site_url = site_url.rstrip("/")
    records = sorted(reg.datatypes.values(), key=lambda r: r["id"])
    names = _term_names(records)
    category_names = {cid: c["name"] for cid, c in reg.categories.items()}

    def path(rid: str) -> str:
        """The dotted name path DataHub resolves ``inherits`` entries by."""
        category = reg.datatypes[rid]["categories"][0]
        return ".".join((ROOT_NAME, category_names.get(category, category), names[rid]))

    by_category: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        iris = fibo_iris(record.get("mappings", {}))
        term: dict[str, Any] = {
            "id": record["id"],
            "name": names[record["id"]],
            "description": record["doc"] or record["name"] or record["id"],
            "term_source": "EXTERNAL",
        }
        if iris:
            term["source_ref"] = "FIBO"
            term["source_url"] = iris[0]
        else:
            term["source_ref"] = ROOT_NAME
            term["source_url"] = record["urls"]["html"]
        inherits = [
            path(target)
            for target in (record.get("semantic_type"), record.get("parent"))
            if target and target in reg.datatypes
        ]
        if inherits:
            term["inherits"] = list(dict.fromkeys(inherits))
        term["custom_properties"] = _custom_properties(record, iris)
        term["knowledge_links"] = _knowledge_links(record)
        by_category.setdefault(record["categories"][0], []).append(term)

    nodes = []
    for category in sorted(by_category, key=lambda c: (category_names.get(c, c), c)):
        terms = sorted(by_category[category], key=lambda t: (t["name"], t["id"]))
        label = category_names.get(category, category)
        nodes.append(
            {
                "id": f"{ROOT_ID}.{category}",
                "name": label,
                "description": f"Semantic data types of the {label} category in the {ROOT_NAME}.",
                "knowledge_links": [{"label": ROOT_NAME, "url": f"{site_url}/category/{category}"}],
                "terms": terms,
            }
        )
    return {
        "version": "1",
        "source": ROOT_NAME,
        "owners": {"users": [DEFAULT_OWNER]},
        "url": site_url,
        "nodes": [
            {
                "id": ROOT_ID,
                "name": ROOT_NAME,
                "description": "Semantic data types (identifiers, codes, personal data) from the "
                f"{ROOT_NAME}: what a column value means and how to recognize it.",
                "knowledge_links": [{"label": ROOT_NAME, "url": site_url}],
                "nodes": nodes,
            }
        ],
    }


def dump_glossary(glossary: dict[str, Any]) -> str:
    """Deterministic YAML: insertion order, no line wrapping, UTF-8 text."""
    return yaml.safe_dump(
        glossary, sort_keys=False, allow_unicode=True, width=float("inf"), default_flow_style=False
    )
