"""Mappings to FIBO, the Financial Industry Business Ontology.

A record maps to a FIBO class with ``mappings.fibo``: the class IRI without the
``https://spec.edmcouncil.org/fibo/ontology/`` prefix, for example
``FBC/ProductsAndServices/ClientsAndAccounts/InternationalBankAccountIdentifier``.

The FIBO server answers 200 for any path under that prefix, so a typo cannot be
caught by a link check. ``fibo update`` therefore reads a checkout of
https://github.com/edmcouncil/fibo and writes ``data/vocabularies/fibo.json``:
the label, definition and maturity of every class that a record maps to, and
the commit it came from. Validation and the build only read that committed
file, so they need no network access.
"""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from collections.abc import Iterable
from pathlib import Path
from typing import Any

FIBO_REPO = "edmcouncil/fibo"
# The term list quotes FIBO labels and definitions, so it carries FIBO's licence.
FIBO_LICENSE = {
    "name": "MIT",
    "copyright": "Copyright (c) Enterprise Data Management Council",
    "url": "https://github.com/edmcouncil/fibo/blob/master/LICENSE",
}
IRI_BASE = "https://spec.edmcouncil.org/fibo/ontology/"
VOCABULARY_FILE = Path("vocabularies") / "fibo.json"
# Domain, modules, ontology, class; the same pattern as in datatype.schema.json.
PATH_RE = re.compile(r"^[A-Z]+/(?:[A-Za-z0-9-]+/)+[A-Za-z0-9]+$")

_RDF = "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}"
_RDFS = "{http://www.w3.org/2000/01/rdf-schema#}"
_OWL = "{http://www.w3.org/2002/07/owl#}"
_SKOS = "{http://www.w3.org/2004/02/skos/core#}"
_XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
_CMNS_AV = "{https://www.omg.org/spec/Commons/AnnotationVocabulary/}"
_MATURITY = "{" + IRI_BASE + "FND/Utilities/AnnotationVocabulary/}hasMaturityLevel"


def iri(path: str) -> str:
    """The IRI of a FIBO class path."""
    return IRI_BASE + path


def normalize(value: str) -> str:
    """A class path from a path or a full FIBO IRI."""
    value = str(value).strip()
    for prefix in (IRI_BASE, IRI_BASE.replace("https://", "http://")):
        if value.startswith(prefix):
            return value[len(prefix) :]
    return value


def fibo_iris(mappings: dict[str, Any]) -> list[str]:
    """The FIBO class IRIs of a record's ``mappings``."""
    value = mappings.get("fibo")
    return [iri(p) for p in (value if isinstance(value, list) else [value] if value else [])]


def mapped_paths(records: Iterable[dict[str, Any]]) -> dict[str, list[str]]:
    """FIBO class path -> ids of the records that map to it."""
    out: dict[str, list[str]] = {}
    for record in records:
        value = (record.get("mappings") or {}).get("fibo")
        for path in value if isinstance(value, list) else [value] if value else []:
            out.setdefault(str(path), []).append(str(record.get("id")))
    return out


def _text(element: ET.Element, tag: str) -> str | None:
    for child in element.findall(tag):
        if child.get(_XML_LANG, "en") == "en" and child.text and child.text.strip():
            return " ".join(child.text.split())
    return None


def scan_classes(fibo_dir: Path) -> dict[str, dict[str, Any]]:
    """Every OWL class of a FIBO checkout, keyed by path, with its English label,
    definition, abbreviations and the maturity level of its ontology.

    A class can be declared in several files; the file that labels it defines it.
    """
    fibo_dir = Path(fibo_dir)
    classes: dict[str, dict[str, Any]] = {}
    for file in sorted(fibo_dir.rglob("*.rdf")):
        relative = file.relative_to(fibo_dir).as_posix()
        if relative.startswith(("etc/", "EXMP/")):
            continue
        try:
            root = ET.parse(file).getroot()
        except ET.ParseError:
            continue
        maturity = None
        ontology = root.find(f"{_OWL}Ontology")
        level = ontology.find(_MATURITY) if ontology is not None else None
        if level is not None:
            maturity = (level.get(f"{_RDF}resource") or "").rsplit("/", 1)[-1] or None
        for element in root.findall(f"{_OWL}Class"):
            about = element.get(f"{_RDF}about") or ""
            if not about.startswith(IRI_BASE):
                continue
            label = _text(element, f"{_RDFS}label")
            if not label:
                continue
            term: dict[str, Any] = {"label": label}
            definition = _text(element, f"{_SKOS}definition")
            if definition:
                term["definition"] = definition
            abbreviations = sorted(
                {a.text.strip() for a in element.findall(f"{_CMNS_AV}abbreviation") if a.text}
            )
            if abbreviations:
                term["abbreviations"] = abbreviations
            if maturity:
                term["maturity"] = maturity
            term["source_file"] = relative
            classes.setdefault(normalize(about), term)
    return classes


def build_vocabulary(
    classes: dict[str, dict[str, Any]], paths: Iterable[str], ref: str
) -> tuple[dict[str, Any], list[str]]:
    """The committed subset of FIBO for ``paths``, and the paths FIBO lacks."""
    paths = sorted(set(paths))
    missing = [p for p in paths if p not in classes]
    terms = {p: classes[p] for p in paths if p in classes}
    source = {"repo": FIBO_REPO, "ref": ref, "iri_base": IRI_BASE, "license": FIBO_LICENSE}
    return {"source": source, "terms": terms}, missing


def vocabulary_path(data_dir: Path) -> Path:
    return Path(data_dir) / VOCABULARY_FILE


def dump_vocabulary(vocabulary: dict[str, Any]) -> str:
    return json.dumps(vocabulary, ensure_ascii=False, indent=1) + "\n"


def load_vocabulary(data_dir: Path) -> dict[str, Any] | None:
    path = vocabulary_path(data_dir)
    if not path.exists():
        return None
    return json.loads(path.read_text("utf-8"))


def search(
    classes: dict[str, dict[str, Any]], query: str, limit: int = 20
) -> list[tuple[str, dict]]:
    """Classes whose path, label or abbreviation contains every word of ``query``."""
    words = query.lower().split()
    hits = []
    for path, term in classes.items():
        haystack = " ".join([path, term["label"], *term.get("abbreviations", [])]).lower()
        if all(w in haystack for w in words):
            hits.append((path, term))
    hits.sort(key=lambda h: (h[1].get("maturity") != "Release", len(h[1]["label"]), h[0]))
    return hits[:limit]
