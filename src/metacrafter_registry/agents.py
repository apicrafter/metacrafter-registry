"""Agent-oriented representations: Markdown twins, llms.txt, RAG corpus, RDF.

All functions take normalized (``/api/v1/``) records, so they work the same on
a fresh build and on a downloaded snapshot.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from .fibo import fibo_iris

RAG_TEMPLATE_VERSION = "1"

DRAFT_NOTE = (
    "Draft records have not been reviewed yet and may be incomplete or wrong; "
    "do not treat them as authoritative for legal or compliance decisions."
)


def _names(ids: Iterable[str], reference: Mapping[str, Mapping[str, Any]] | None) -> str:
    ids = list(ids)
    if reference is None:
        return ", ".join(ids)
    return ", ".join(f"{reference[i]['name']} ({i})" if i in reference else i for i in ids)


def _yaml_scalar(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value)
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def record_markdown(
    record: Mapping[str, Any],
    *,
    categories: Mapping[str, Mapping[str, Any]] | None = None,
    countries: Mapping[str, Mapping[str, Any]] | None = None,
    langs: Mapping[str, Mapping[str, Any]] | None = None,
) -> str:
    """Markdown with YAML front matter: the same facts as the HTML record page."""
    front = [
        ("id", record["id"]),
        ("kind", record["kind"]),
        ("status", record["status"]),
        ("is_pii", record["is_pii"]),
    ]
    lines = ["---"]
    lines += [f"{key}: {_yaml_scalar(value)}" for key, value in front]
    for key in ("categories", "country", "langs", "aliases"):
        if record.get(key):
            lines.append(f"{key}: [{', '.join(_yaml_scalar(v) for v in record[key])}]")
    lines.append(f"quality: {record['quality']['score']}")
    lines.append(f"url: {_yaml_scalar(record['urls']['html'])}")
    lines += ["---", "", f"# {record['name']} (`{record['id']}`)", ""]
    if record["status"] == "draft":
        lines += [f"> **Draft.** {DRAFT_NOTE}", ""]
    elif record["status"] == "deprecated":
        replaced = record.get("replaced_by")
        lines += [f"> **Deprecated.**{f' Use `{replaced}` instead.' if replaced else ''}", ""]
    lines += [record["doc"], ""]

    facts = []
    if record.get("semantic_type"):
        facts.append(f"- Pattern of: `{record['semantic_type']}`")
    if record.get("parent"):
        facts.append(f"- Parent datatype: `{record['parent']}`")
    facts.append(f"- Personal data (PII): {'yes' if record['is_pii'] else 'no'}")
    if record.get("categories"):
        facts.append(f"- Categories: {_names(record['categories'], categories)}")
    facts.append(
        "- Countries: "
        + (_names(record["country"], countries) if record.get("country") else "global")
    )
    if record.get("langs"):
        facts.append(f"- Languages: {_names(record['langs'], langs)}")
    if record.get("classification"):
        facts.append(f"- Classification: {record['classification']}")
    if record.get("aliases"):
        facts.append(f"- Former IDs: {', '.join(f'`{a}`' for a in record['aliases'])}")
    if record.get("patterns"):
        facts.append(f"- Patterns: {', '.join(f'`{p}`' for p in record['patterns'])}")
    lines += facts + [""]

    if record.get("regexp") or record.get("checksum"):
        lines += ["## Detection", ""]
        if record.get("regexp"):
            lines += ["Regular expression (Python `re`):", "", "```", record["regexp"], "```", ""]
        if record.get("checksum"):
            lines += [f"Check digit algorithm: `{record['checksum']}`", ""]
    if record.get("examples"):
        lines += ["## Examples", ""]
        for example in record["examples"]:
            mark = "" if example.get("valid", True) else " (invalid example)"
            note = f" — {example['description']}" if example.get("description") else ""
            lines.append(f"- `{example['value']}`{mark}{note}")
        lines.append("")
    if record.get("mappings"):
        lines += ["## Mappings", ""]
        for system, value in record["mappings"].items():
            values = value if isinstance(value, list) else [value]
            if system == "fibo":  # paths are only meaningful as IRIs
                iris = fibo_iris(record["mappings"])
                lines.append(f"- fibo: {', '.join(f'<{iri}>' for iri in iris)}")
                continue
            lines.append(f"- {system}: {', '.join(f'`{v}`' for v in values)}")
        lines.append("")
    rules = record.get("detected_by", {}).get("metacrafter_rules", [])
    if rules:
        by_type = {kind: sum(1 for r in rules if r["type"] == kind) for kind in ("field", "data")}
        lines += [
            "## Metacrafter rules",
            "",
            f"{len(rules)} rules: {by_type['field']} match the field name, "
            f"{by_type['data']} match values.",
            "",
        ]
        lines += [f"- `{r['rule']}` ({r['type']}, `{r['file']}`)" for r in rules[:20]] + [""]
    if record.get("detected_by", {}).get("tools"):
        lines += ["## Supported by tools", ""]
        lines += [f"- `{t}`" for t in record["detected_by"]["tools"]] + [""]
    if record.get("translations"):
        lines += ["## Translations", ""]
        for lang, t in record["translations"].items():
            doc = f": {t['doc']}" if t.get("doc") else ""
            lines.append(f"- {lang}: {t.get('name', '')}{doc}")
        lines.append("")
    if record.get("links"):
        lines += ["## Sources", ""]
        lines += [f"- {link['type']}: <{link['url']}>" for link in record["links"]] + [""]
    missing = record["quality"]["missing"]
    lines += [
        "## Quality",
        "",
        f"Score {record['quality']['score']}/100."
        + (f" Missing: {', '.join(missing)}." if missing else ""),
        "",
        f"JSON: <{record['urls']['json']}> · Edit: <{record['source']['edit_url']}>",
        "",
    ]
    return "\n".join(lines)


def tool_markdown(tool: Mapping[str, Any]) -> str:
    lines = [
        "---",
        f"id: {_yaml_scalar(tool['id'])}",
        f"category: {_yaml_scalar(tool['category'])}",
        f"url: {_yaml_scalar(tool['urls']['html'])}",
        "---",
        "",
        f"# {tool['name']} (`{tool['id']}`)",
        "",
        tool["doc"],
        "",
    ]
    if tool.get("website"):
        lines += [f"Website: <{tool['website']}>", ""]
    if tool.get("supported_types"):
        lines += [f"## Supported datatypes ({len(tool['supported_types'])})", ""]
        lines += [f"- `{t}`" for t in tool["supported_types"]] + [""]
    return "\n".join(lines)


def rag_text(record: Mapping[str, Any]) -> str:
    """The text an embedding index should use for a record (template version 1)."""
    parts = [
        f"Name: {record['name']}",
        f"ID: {record['id']}",
        f"Kind: {record['kind']}",
        f"Description: {record['doc']}",
    ]
    if record.get("aliases"):
        parts.append(f"Also known as: {', '.join(record['aliases'])}")
    names = [t["name"] for t in record.get("translations", {}).values() if t.get("name")]
    if names:
        parts.append(f"Translated names: {'; '.join(names)}")
    if record.get("categories"):
        parts.append(f"Categories: {', '.join(record['categories'])}")
    parts.append(f"Countries: {', '.join(record.get('country', [])) or 'global'}")
    if record.get("langs"):
        parts.append(f"Languages: {', '.join(record['langs'])}")
    parts.append(f"Personal data: {'yes' if record['is_pii'] else 'no'}")
    examples = [e["value"] for e in record.get("examples", []) if e.get("valid", True)]
    if examples:
        parts.append(f"Examples: {', '.join(examples[:5])}")
    if record.get("regexp"):
        parts.append(f"Regexp: {record['regexp']}")
    return "\n".join(parts)


def rag_entry(record: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "id": record["id"],
        "text": rag_text(record),
        "metadata": {
            "kind": record["kind"],
            "status": record["status"],
            "is_pii": record["is_pii"],
            "categories": record.get("categories", []),
            "country": record.get("country", []),
            "langs": record.get("langs", []),
            "quality": record["quality"]["score"],
            "url": record["urls"]["html"],
        },
    }


def llms_txt(
    site_url: str,
    counts: Mapping[str, int],
    categories: Iterable[Mapping[str, Any]],
    countries: Iterable[Mapping[str, Any]],
) -> str:
    """/llms.txt following https://llmstxt.org."""
    s = site_url
    lines = [
        "# Metacrafter Registry",
        "",
        f"> Open registry of {counts['datatypes']} semantic datatypes and {counts['patterns']} "
        "patterns: identifiers, personal data (PII), codes and classifiers. Records have a "
        "description and, where known, a regular expression, examples, a check-digit algorithm, "
        "links to Wikidata and Schema.org, and the tools that detect them. Metacrafter uses "
        "these ids to label fields of tables and data files.",
        "",
        "Every record has a `status`. " + DRAFT_NOTE + " Each record also has a quality score "
        "(0-100). Record pages have Markdown twins: append `.md` to any `/datatype/<id>` URL.",
        "",
        "## Docs",
        "",
        f"- [For AI agents]({s}/agents.md): MCP server, Python package, skills, labeling columns",
        f"- [About and API]({s}/about): data model, statuses, license, contributing",
        f"- [OpenAPI 3.1]({s}/api/v1/openapi.json): every static JSON endpoint",
        "",
        "## Data",
        "",
        f"- [Manifest]({s}/api/v1/index.json): version, counts, SHA-256 of every bulk file",
        f"- [All records, Markdown]({s}/llms-full.txt): every datatype and pattern in one file",
        f"- [All records, JSONL]({s}/api/v1/datatypes.jsonl): normalized records",
        f"- [RAG corpus]({s}/api/v1/rag/corpus.jsonl): one embedding text per record",
        f"- [Aliases]({s}/api/v1/aliases.json): retired ids and the record each resolves to",
        f"- [SKOS concept scheme]({s}/registry.ttl): linked-data export (Turtle); "
        "one record: `/datatype/<id>.ttl`",
        f"- [RDF vocabulary]({s}/vocab.ttl): OWL declaration of the `mcr:` terms",
        "",
        "## Categories",
        "",
    ]
    lines += [
        f"- [{c['name']}]({s}/category/{c['id']}.md): {c['count']} records" for c in categories
    ]
    lines += ["", "## Optional", ""]
    lines += [f"- [{c['name']}]({s}/country/{c['id']}): {c['count']} records" for c in countries]
    return "\n".join(lines) + "\n"


def llms_full_txt(records: Iterable[Mapping[str, Any]], site_url: str) -> str:
    """All records as compact Markdown, one section each."""
    out = [
        "# Metacrafter Registry: all datatypes and patterns",
        "",
        f"Source: {site_url}. {DRAFT_NOTE}",
        "",
    ]
    for r in records:
        facts = [
            f"id `{r['id']}`",
            r["kind"],
            r["status"],
            "PII" if r["is_pii"] else "not PII",
            "countries " + (", ".join(r.get("country", [])) or "global"),
        ]
        if r.get("categories"):
            facts.append("categories " + ", ".join(r["categories"]))
        if r.get("semantic_type"):
            facts.append(f"pattern of `{r['semantic_type']}`")
        if r.get("aliases"):
            facts.append("aliases " + ", ".join(r["aliases"]))
        out += [f"## {r['name']}", "", "; ".join(facts) + ".", "", r["doc"], ""]
        if r.get("regexp"):
            out += [
                f"Regexp: `{r['regexp']}`"
                + (f"; check digit: {r['checksum']}" if r.get("checksum") else ""),
                "",
            ]
        examples = [e["value"] for e in r.get("examples", []) if e.get("valid", True)]
        if examples:
            out += ["Examples: " + ", ".join(f"`{e}`" for e in examples[:5]), ""]
        out += [f"<{r['urls']['html']}>", ""]
    return "\n".join(out)


def category_markdown(
    category: Mapping[str, Any], records: Iterable[Mapping[str, Any]], site_url: str
) -> str:
    lines = [f"# {category['name']} (`{category['id']}`)", "", f"{category['count']} records.", ""]
    for r in records:
        status = "" if r["status"] == "stable" else f" [{r['status']}]"
        lines.append(f"- [{r['name']}]({site_url}/datatype/{r['id']}.md) `{r['id']}`{status}")
    return "\n".join(lines) + "\n"


# --- RDF (Turtle) ----------------------------------------------------------

#: The registry vocabulary (prefix ``mcr:``, namespace ``<site>/vocab#``).
#: Terms are added, never removed or renamed.
VOCAB_TERMS: tuple[dict[str, str], ...] = (
    {
        "name": "Tool",
        "kind": "owl:Class",
        "label": "tool",
        "comment": "Software that detects, masks or catalogs values of registry datatypes. "
        "Each tool is described at /tool/<id>.",
    },
    {
        "name": "supportedType",
        "kind": "owl:ObjectProperty",
        "domain": "mcr:Tool",
        "range": "skos:Concept",
        "label": "supported type",
        "comment": "A registry datatype or pattern that the tool supports.",
    },
    {
        "name": "status",
        "kind": "owl:DatatypeProperty",
        "domain": "skos:Concept",
        "range": "xsd:string",
        "label": "status",
        "comment": "Review status of the record: draft (not reviewed yet), stable (reviewed) "
        "or deprecated.",
    },
    {
        "name": "isPII",
        "kind": "owl:DatatypeProperty",
        "domain": "skos:Concept",
        "range": "xsd:boolean",
        "label": "is personal data",
        "comment": "True when values of this type are personal data (PII).",
    },
    {
        "name": "classification",
        "kind": "owl:DatatypeProperty",
        "domain": "skos:Concept",
        "range": "xsd:string",
        "label": "classification",
        "comment": "identifier when a value identifies an entity, categorical when values "
        "come from a closed list of codes or categories.",
    },
    {
        "name": "regexp",
        "kind": "owl:DatatypeProperty",
        "domain": "skos:Concept",
        "range": "xsd:string",
        "label": "regular expression",
        "comment": "Regular expression in Python re syntax that a whole value matches, "
        "usually anchored with ^ and $. It is not an XML Schema or XPath pattern.",
    },
    {
        "name": "checksum",
        "kind": "owl:DatatypeProperty",
        "domain": "skos:Concept",
        "range": "xsd:string",
        "label": "check-digit algorithm",
        "comment": "Name of the check-digit algorithm that validates a value, for example "
        "luhn or iban_mod97.",
    },
)

_DPV_PREFIXES = {"pd": "https://w3id.org/dpv/pd#", "dpv": "https://w3id.org/dpv#"}
_ISO639_1 = "http://id.loc.gov/vocabulary/iso639-1/"
_IRI_UNSAFE = set('<>"{}|^`\\ ')


def _ttl_literal(text: str, lang: str | None = None) -> str:
    escaped = (
        str(text)
        .replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")
    )
    return f'"{escaped}"' + (f"@{lang}" if lang else "")


def _ttl_iri(iri: str) -> str:
    if any(c in _IRI_UNSAFE or ord(c) < 0x20 for c in iri):
        raise ValueError(f"cannot use {iri!r} as an IRI")
    return f"<{iri}>"


def _ttl_url(url: str) -> str:
    """A web address as an IRI, percent-encoding the characters Turtle forbids."""
    return _ttl_iri(
        "".join(f"%{ord(c):02X}" if c in _IRI_UNSAFE or ord(c) < 0x20 else c for c in url)
    )


def _as_list(value: Any) -> list:
    return value if isinstance(value, list) else [value] if value else []


def _schema_org_iri(value: str) -> str:
    if value.startswith("http://schema.org/"):
        return "https://schema.org/" + value[len("http://schema.org/") :]
    return value if value.startswith("http") else f"https://schema.org/{value}"


def _dpv_iri(value: str) -> str | None:
    if value.startswith("http"):
        return value
    prefix, _, local = value.partition(":")
    return _DPV_PREFIXES[prefix] + local if prefix in _DPV_PREFIXES and local else None


def _match_links(mappings: Mapping[str, Any]) -> list[tuple[str, str]]:
    """(SKOS mapping predicate, IRI) for every mapping that names a concept by IRI."""
    links: list[tuple[str, str]] = []

    def add(predicate: str, iri: str | None) -> None:
        if iri and all(iri != seen for _, seen in links):
            links.append((predicate, iri))

    if mappings.get("wikidata"):
        add("skos:exactMatch", f"http://www.wikidata.org/entity/{mappings['wikidata']}")
    for value in _as_list(mappings.get("schema_org")) + _as_list(mappings.get("d3m")):
        add("skos:exactMatch", _schema_org_iri(value))
    for iri in fibo_iris(mappings):
        add("skos:exactMatch", iri)
    for prefix in _as_list(mappings.get("bioregistry")):
        add("skos:exactMatch", f"https://bioregistry.io/registry/{prefix}")
    for value in _as_list(mappings.get("fhir")):
        add("skos:exactMatch", value)
    for value in _as_list(mappings.get("dpv")):
        add("skos:broadMatch", _dpv_iri(value))
    return links


def _turtle_prefixes(site_url: str) -> list[str]:
    prefixes = {
        "skos": "http://www.w3.org/2004/02/skos/core#",
        "dcterms": "http://purl.org/dc/terms/",
        "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
        "owl": "http://www.w3.org/2002/07/owl#",
        "xsd": "http://www.w3.org/2001/XMLSchema#",
        "foaf": "http://xmlns.com/foaf/0.1/",
        "mcr": f"{site_url}/vocab#",
        "dt": f"{site_url}/datatype/",
        "cat": f"{site_url}/category/",
        "country": f"{site_url}/country/",
        "tool": f"{site_url}/tool/",
    }
    return [f"@prefix {p}: <{iri}> ." for p, iri in prefixes.items()] + [""]


def _is_top_concept(r: Mapping[str, Any]) -> bool:
    return not r.get("semantic_type") and not r.get("parent")


def _concept_turtle(r: Mapping[str, Any], site_url: str) -> str:
    """The description of one datatype or pattern as a ``skos:Concept``."""
    scheme = _ttl_iri(f"{site_url}/")
    props = ["a skos:Concept", f"skos:inScheme {scheme}"]
    if _is_top_concept(r):
        props.append(f"skos:topConceptOf {scheme}")
    props += [
        f"skos:notation {_ttl_literal(r['id'])}",
        f"skos:prefLabel {_ttl_literal(r['name'], 'en')}",
        f"skos:definition {_ttl_literal(r['doc'], 'en')}",
    ]
    for lang, t in r.get("translations", {}).items():
        if lang == "en":
            continue
        if t.get("name"):
            props.append(f"skos:prefLabel {_ttl_literal(t['name'], lang)}")
        if t.get("doc"):
            props.append(f"skos:definition {_ttl_literal(t['doc'], lang)}")
    for alias in r.get("aliases", []):
        props.append(f"skos:altLabel {_ttl_literal(alias)}")
    for broader in filter(None, (r.get("semantic_type"), r.get("parent"))):
        props.append(f"skos:broader dt:{broader}")
    for narrower in r.get("patterns", []) + r.get("children", []):
        props.append(f"skos:narrower dt:{narrower}")
    for predicate, iri in _match_links(r.get("mappings", {})):
        props.append(f"{predicate} {_ttl_iri(iri)}")
    for example in r.get("examples", []):
        if example.get("valid", True):
            props.append(f"skos:example {_ttl_literal(example['value'])}")
    props.append(f"mcr:status {_ttl_literal(r['status'])}")
    props.append(f"mcr:isPII {'true' if r['is_pii'] else 'false'}")
    for field in ("classification", "regexp", "checksum"):
        if r.get(field):
            props.append(f"mcr:{field} {_ttl_literal(r[field])}")
    for code in r.get("country", []):
        props.append(f"dcterms:spatial country:{code}")
    for lang in r.get("langs", []):
        if lang != "common":
            props.append(f"dcterms:language {_ttl_iri(_ISO639_1 + lang)}")
    for link in r.get("links", []):
        props.append(f"rdfs:seeAlso {_ttl_url(link['url'])}")
    if r["status"] == "deprecated":
        props.append("owl:deprecated true")
    if r.get("replaced_by"):
        props.append(f"dcterms:isReplacedBy dt:{r['replaced_by']}")
    return f"dt:{r['id']} " + " ;\n    ".join(props) + " .\n"


def _tool_turtle(tool: Mapping[str, Any], canonical: Mapping[str, str]) -> str:
    props = ["a mcr:Tool", f"rdfs:label {_ttl_literal(tool['name'], 'en')}"]
    if tool.get("doc"):
        props.append(f"dcterms:description {_ttl_literal(tool['doc'], 'en')}")
    if tool.get("website"):
        props.append(f"foaf:homepage {_ttl_url(tool['website'])}")
    supported = dict.fromkeys(
        canonical[t] for t in tool.get("supported_types", []) if t in canonical
    )
    props += [f"mcr:supportedType dt:{t}" for t in supported]
    return f"tool:{tool['id']} " + " ;\n    ".join(props) + " .\n"


def skos_turtle(
    records: Iterable[Mapping[str, Any]],
    categories: Iterable[Mapping[str, Any]],
    site_url: str,
    version: str,
    tools: Iterable[Mapping[str, Any]] = (),
) -> str:
    """``/registry.ttl``: the concept scheme, its collections and the tools."""
    records = list(records)
    tops = [r["id"] for r in records if _is_top_concept(r)]
    scheme = [
        "a skos:ConceptScheme",
        f"dcterms:title {_ttl_literal('Metacrafter Registry', 'en')}",
        f"dcterms:hasVersion {_ttl_literal(version)}",
    ]
    if tops:
        scheme.append("skos:hasTopConcept " + ",\n        ".join(f"dt:{t}" for t in tops))
    lines = _turtle_prefixes(site_url)
    lines += [f"{_ttl_iri(site_url + '/')} " + " ;\n    ".join(scheme) + " .", ""]
    lines += [_concept_turtle(r, site_url) for r in records]
    for c in categories:
        members = [r["id"] for r in records if c["id"] in r.get("categories", [])]
        if not members:
            continue
        props = ["a skos:Collection", f"skos:prefLabel {_ttl_literal(c['name'], 'en')}"]
        props += [f"skos:member dt:{m}" for m in members]
        lines.append(f"cat:{c['id']} " + " ;\n    ".join(props) + " .")
        lines.append("")
    canonical = {r["id"]: r["id"] for r in records}
    canonical.update({a: r["id"] for r in records for a in r.get("aliases", [])})
    lines += [_tool_turtle(t, canonical) for t in tools]
    return "\n".join(lines)


def record_turtle(record: Mapping[str, Any], site_url: str) -> str:
    """``/datatype/<id>.ttl``: one record, with the same triples as in ``/registry.ttl``."""
    return "\n".join(_turtle_prefixes(site_url) + [_concept_turtle(record, site_url)])


def vocab_turtle(site_url: str) -> str:
    """``/vocab.ttl``: the OWL declaration of the ``mcr:`` terms."""
    ontology = _ttl_iri(f"{site_url}/vocab")
    lines = _turtle_prefixes(site_url)
    header = [
        "a owl:Ontology",
        f"dcterms:title {_ttl_literal('Metacrafter Registry vocabulary', 'en')}",
        "dcterms:description "
        + _ttl_literal(
            "Terms that describe how to recognize values of the registry's datatypes, "
            "and the tools that support them. Used in /registry.ttl and /datatype/<id>.ttl.",
            "en",
        ),
        f"rdfs:seeAlso {_ttl_iri(site_url + '/registry.ttl')}",
    ]
    lines += [f"{ontology} " + " ;\n    ".join(header) + " .", ""]
    for term in VOCAB_TERMS:
        props = [
            f"a {term['kind']}",
            f"rdfs:label {_ttl_literal(term['label'], 'en')}",
            f"rdfs:comment {_ttl_literal(term['comment'], 'en')}",
            f"rdfs:isDefinedBy {ontology}",
        ]
        if term.get("domain"):
            props.append(f"rdfs:domain {term['domain']}")
        if term.get("range"):
            props.append(f"rdfs:range {term['range']}")
        lines += [f"mcr:{term['name']} " + " ;\n    ".join(props) + " .", ""]
    return "\n".join(lines)


# --- browser identification index -----------------------------------------

_INLINE_FLAGS = {"i": "i", "s": "s", "m": "m"}


def js_regexp(pattern: str) -> tuple[str, str] | None:
    """Translate a Python ``re`` pattern to ECMAScript, or None if it cannot be."""
    import re as _re

    flags = ""
    lead = _re.match(r"^\(\?([a-zA-Z]+)\)", pattern)
    if lead:
        for flag in lead.group(1):
            if flag not in _INLINE_FLAGS:
                return None
            flags += _INLINE_FLAGS[flag]
        pattern = pattern[lead.end() :]
    if _re.search(r"\(\?[aiLmsux]+[):]", pattern) or "(?#" in pattern:
        return None  # inline flags inside the pattern, comments
    pattern = pattern.replace("(?P<", "(?<")
    pattern = _re.sub(r"\(\?P=(\w+)\)", r"\\k<\1>", pattern)
    # \A and \Z, but not an escaped backslash followed by A or Z.
    pattern = _re.sub(r"(?<!\\)((?:\\\\)*)\\A", r"\1^", pattern)
    pattern = _re.sub(r"(?<!\\)((?:\\\\)*)\\Z", r"\1$", pattern)
    return pattern, flags


def identify_index(records: Iterable[Mapping[str, Any]], broadness: Mapping[str, float]) -> list:
    """Compact records for the /identify page (all records; regexps in JS syntax)."""
    out = []
    for r in records:
        entry: dict[str, Any] = {"id": r["id"], "n": r["name"], "s": r["status"], "p": r["is_pii"]}
        if r.get("country"):
            entry["c"] = r["country"]
        if r.get("aliases"):
            entry["a"] = r["aliases"]
        names = [t["name"] for t in r.get("translations", {}).values() if t.get("name")]
        if names:
            entry["t"] = names
        if r.get("regexp"):
            converted = js_regexp(r["regexp"])
            if converted:
                entry["re"], flags = converted
                if flags:
                    entry["f"] = flags
                entry["b"] = round(broadness.get(r["id"], 0.0), 3)
        if r.get("checksum"):
            entry["ck"] = r["checksum"]
        out.append(entry)
    return out
