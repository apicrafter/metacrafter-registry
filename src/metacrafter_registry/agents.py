"""Agent-oriented representations: Markdown twins, llms.txt, RAG corpus, SKOS.

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
        f"- [SKOS concept scheme]({s}/registry.ttl): linked-data export (Turtle)",
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


# --- SKOS (Turtle) ---------------------------------------------------------


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
    bad = set('<>"{}|^`\\ ')
    if any(c in bad for c in iri):
        raise ValueError(f"cannot use {iri!r} as an IRI")
    return f"<{iri}>"


def _match_iris(mappings: Mapping[str, Any]) -> list[str]:
    iris = []
    wikidata = mappings.get("wikidata")
    if wikidata:
        iris.append(f"http://www.wikidata.org/entity/{wikidata}")
    schema_org = mappings.get("schema_org")
    for value in schema_org if isinstance(schema_org, list) else [schema_org] if schema_org else []:
        iris.append(value if value.startswith("http") else f"https://schema.org/{value}")
    iris += fibo_iris(mappings)
    return iris


def skos_turtle(
    records: Iterable[Mapping[str, Any]],
    categories: Iterable[Mapping[str, Any]],
    site_url: str,
    version: str,
) -> str:
    scheme = f"{site_url}/"
    records = list(records)
    lines = [
        "@prefix skos: <http://www.w3.org/2004/02/skos/core#> .",
        "@prefix dcterms: <http://purl.org/dc/terms/> .",
        f"@prefix dt: <{site_url}/datatype/> .",
        f"@prefix cat: <{site_url}/category/> .",
        "",
        f"{_ttl_iri(scheme)} a skos:ConceptScheme ;",
        f"    dcterms:title {_ttl_literal('Metacrafter Registry', 'en')} ;",
        f"    dcterms:hasVersion {_ttl_literal(version)} .",
        "",
    ]
    for r in records:
        props = [
            "a skos:Concept",
            f"skos:inScheme {_ttl_iri(scheme)}",
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
        for iri in _match_iris(r.get("mappings", {})):
            props.append(f"skos:exactMatch {_ttl_iri(iri)}")
        lines.append(f"dt:{r['id']} " + " ;\n    ".join(props) + " .")
        lines.append("")
    for c in categories:
        members = [r["id"] for r in records if c["id"] in r.get("categories", [])]
        if not members:
            continue
        props = ["a skos:Collection", f"skos:prefLabel {_ttl_literal(c['name'], 'en')}"]
        props += [f"skos:member dt:{m}" for m in members]
        lines.append(f"cat:{c['id']} " + " ;\n    ".join(props) + " .")
        lines.append("")
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
