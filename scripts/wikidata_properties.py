#!/usr/bin/env python3
"""Compare the registry with the Wikidata external-identifier properties.

Wikidata has more than 10,000 properties of type "external identifier". Most of
them describe one value format: a label, a description, a format regexp
(P1793), example values (P1855) and a formatter URL (P1630). This script
downloads that data and compares it with the registry (issue #19).

    python scripts/wikidata_properties.py fetch
    python scripts/wikidata_properties.py report > report.md

``fetch`` writes ``wikidata_properties.json`` (about 15 MB, not committed). It
uses the Wikidata Query Service and the property usage report
https://www.wikidata.org/wiki/Wikidata:Database_reports/List_of_properties/all.
The usage counts in that report can lag behind Wikidata.

``report`` prints a Markdown report:

1. mappings.wikidata values that are not external-identifier properties, with
   the property label, so that a person can check the mapping;
2. mapped records that lack a regexp or examples that Wikidata has, and
   Wikidata examples that do not match the record regexp;
3. external-identifier properties of the selected Wikidata classes that no
   record maps to, most used first.

The report is a list of leads, not facts to copy. Check every regexp and
example before you add it to a record: see skills/registry-contributor.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from metacrafter_registry.loader import load_sources  # noqa: E402

SPARQL = "https://query.wikidata.org/sparql"
USAGE_PAGE = (
    "https://www.wikidata.org/w/index.php?"
    "title=Wikidata:Database_reports/List_of_properties/all&action=raw"
)
USER_AGENT = "metacrafter-registry/wikidata_properties (https://github.com/apicrafter/metacrafter-registry)"
DEFAULT_FILE = "wikidata_properties.json"

# Wikidata classes of properties (P31 values) that name identifiers which
# appear in datasets: codes of standards, registers, classifications and
# databases rather than profile pages of web sites.
DEFAULT_CLASSES = {
    "Q27038669": "international standard identifier",
    "Q26235166": "organizations in company registers",
    "Q55977691": "administrative subdivisions",
    "Q108566342": "classification schemes",
    "Q19833835": "substances",
    "Q19887775": "medicine",
    "Q42396390": "taxa",
    "Q29548341": "scholarly articles",
    "Q96776953": "libraries",
    "Q140831665": "educational institutions",
    "Q135984095": "European Union",
    "Q105388954": "online accounts",
}

QUERIES = {
    "props": """SELECT ?p ?label ?desc WHERE { ?p wikibase:propertyType wikibase:ExternalId .
        OPTIONAL { ?p rdfs:label ?label FILTER(lang(?label)="en") }
        OPTIONAL { ?p schema:description ?desc FILTER(lang(?desc)="en") } }""",
    "regex": """SELECT ?p ?v WHERE { ?p wikibase:propertyType wikibase:ExternalId ; wdt:P1793 ?v }""",
    "formatter": """SELECT ?p ?v WHERE { ?p wikibase:propertyType wikibase:ExternalId ; wdt:P1630 ?v }""",
    "classes": """SELECT ?p ?v WHERE { ?p wikibase:propertyType wikibase:ExternalId ; wdt:P31 ?v }""",
    "country": """SELECT ?p ?v WHERE { ?p wikibase:propertyType wikibase:ExternalId ;
        wdt:P17 ?c . ?c wdt:P297 ?v }""",
    "examples": """SELECT ?p ?item ?v WHERE { ?p wikibase:propertyType wikibase:ExternalId ;
        wikibase:qualifier ?pq ; p:P1855 ?st . ?st ps:P1855 ?item ; ?pq ?v }""",
}


def _get(url: str, accept: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": accept})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(request, timeout=300) as response:
                return response.read().decode("utf-8")
        except OSError as exc:  # HTTP 429/5xx and timeouts: back off and retry
            print(f"retry {attempt + 1}: {exc}", file=sys.stderr)
            time.sleep(10 * (attempt + 1))
    raise SystemExit(f"cannot fetch {url}")


def _sparql_rows(query: str) -> list[dict[str, str]]:
    url = SPARQL + "?" + urllib.parse.urlencode({"query": query})
    text = _get(url, "text/csv")
    return list(csv.DictReader(io.StringIO(text)))


def _entity(uri: str) -> str:
    return uri.rsplit("/", 1)[-1]


def fetch(out: Path) -> None:
    props: dict[str, dict] = {}
    for row in _sparql_rows(QUERIES["props"]):
        pid = _entity(row["p"])
        props[pid] = {
            "id": pid,
            "label": row["label"],
            "description": row["desc"],
            "regex": [],
            "formatter": [],
            "classes": [],
            "country": [],
            "examples": [],
            "usage": None,
        }
    for key in ("regex", "formatter", "classes", "country"):
        for row in _sparql_rows(QUERIES[key]):
            prop = props.get(_entity(row["p"]))
            value = _entity(row["v"]) if key == "classes" else row["v"]
            if prop is not None and value not in prop[key]:
                prop[key].append(value)
    for row in _sparql_rows(QUERIES["examples"]):
        prop = props.get(_entity(row["p"]))
        if prop is not None:
            prop["examples"].append({"item": _entity(row["item"]), "value": row["v"]})
    line_re = re.compile(r"\|\[\[P:(P\d+)\|P\d+\]\]\|\|.*\|\|EI\|\|(.*)$")
    for line in _get(USAGE_PAGE, "text/plain").splitlines():
        match = line_re.match(line)
        if match and match.group(1) in props:
            main = re.search(r"([\d,]+) M", match.group(2))
            props[match.group(1)]["usage"] = int(main.group(1).replace(",", "")) if main else 0
    out.write_text(json.dumps(props, ensure_ascii=False, indent=1), "utf-8")
    print(f"{len(props)} external-identifier properties written to {out}", file=sys.stderr)


def report(props_file: Path, classes: dict[str, str], limit: int) -> None:
    props = json.loads(props_file.read_text("utf-8"))
    sources = load_sources(ROOT / "data")
    mapped: dict[str, list[str]] = {}
    lines = ["# Registry and Wikidata external-identifier properties", ""]

    lines += ["## 1. Mappings to check", ""]
    lines += ["Values of `mappings.wikidata` that are not external-identifier properties.", ""]
    for rec in sorted(sources.datatypes, key=lambda r: r.id):
        pid = (rec.data.get("mappings") or {}).get("wikidata")
        if not pid:
            continue
        mapped.setdefault(pid, []).append(rec.id)
        if pid not in props:
            lines.append(f"- `{rec.id}` ({rec.data.get('name')}) -> {pid}")
    lines.append("")

    lines += ["## 2. Data that Wikidata has for mapped records", ""]
    for rec in sorted(sources.datatypes, key=lambda r: r.id):
        pid = (rec.data.get("mappings") or {}).get("wikidata")
        prop = props.get(pid or "")
        if not prop:
            continue
        notes = []
        regexp = rec.data.get("regexp")
        positive = [e for e in rec.data.get("examples") or [] if e.get("valid", True)]
        if not regexp and prop["regex"]:
            notes.append(f"no regexp; Wikidata: `{prop['regex'][0]}`")
        if not positive and prop["examples"]:
            values = ", ".join(f"`{e['value']}`" for e in prop["examples"][:3])
            notes.append(f"no examples; Wikidata: {values}")
        if regexp and prop["examples"]:
            try:
                compiled = re.compile(str(regexp))
            except re.error:
                compiled = None
            if compiled is not None:
                bad = [e["value"] for e in prop["examples"] if not compiled.search(e["value"])]
                if bad:
                    values = ", ".join(f"`{v}`" for v in bad[:3])
                    notes.append(f"Wikidata examples that do not match the regexp: {values}")
        if notes:
            lines.append(f"- `{rec.id}` -> {pid} {prop['label']}: " + "; ".join(notes))
    lines.append("")

    lines += ["## 3. Unmapped properties", ""]
    for qid, title in classes.items():
        rows = [p for p in props.values() if qid in p["classes"] and p["id"] not in mapped]
        rows.sort(key=lambda p: -(p["usage"] or 0))
        lines += [f"### {title} ({qid}): {len(rows)}", ""]
        lines += ["| Property | Label | Uses | Country | Regexp | Wikidata example |"]
        lines += ["|---|---|---:|---|---|---|"]
        for prop in rows[:limit]:
            regex = (prop["regex"] or [""])[0].replace("|", "\\|")
            example = prop["examples"][0]["value"] if prop["examples"] else ""
            usage = "" if prop["usage"] is None else prop["usage"]
            lines.append(
                f"| {prop['id']} | {prop['label']} | {usage} | {','.join(prop['country'])} "
                f"| `{regex}` | `{example}` |"
            )
        lines.append("")
    print("\n".join(lines))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("fetch", help="download external-identifier property data")
    p.add_argument("--out", type=Path, default=Path(DEFAULT_FILE))
    p = sub.add_parser("report", help="print a Markdown comparison with the registry")
    p.add_argument("--props", type=Path, default=Path(DEFAULT_FILE))
    p.add_argument("--class", dest="classes", action="append", metavar="QID",
                   help="Wikidata property class to list (repeatable); default: a built-in set")
    p.add_argument("--limit", type=int, default=40, help="rows per class (default 40)")
    args = parser.parse_args(argv)
    if args.command == "fetch":
        fetch(args.out)
    else:
        classes = {q: q for q in args.classes} if args.classes else DEFAULT_CLASSES
        report(args.props, classes, args.limit)
    return 0


if __name__ == "__main__":
    sys.exit(main())
