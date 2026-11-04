from __future__ import annotations

import json

import pytest


def test_llms_txt(built_site):
    text = (built_site / "llms.txt").read_text("utf-8")
    assert text.startswith("# Metacrafter Registry\n\n> ")
    for link in ("/agents.md", "/api/v1/openapi.json", "/api/v1/index.json", "/llms-full.txt"):
        assert f"https://registry.apicrafter.io{link}" in text
    assert "Draft records have not been reviewed" in text
    full = (built_site / "llms-full.txt").read_text("utf-8")
    assert "## Email (Electronic mail)" in full and "id `email`" in full


def test_markdown_twins(built_site):
    md = (built_site / "datatype/email.md").read_text("utf-8")
    assert md.startswith('---\nid: "email"\nkind: "datatype"\nstatus: "stable"\nis_pii: true\n')
    assert "## Detection" in md and "Regular expression" in md
    assert (built_site / "tool/presidio.md").is_file()
    assert (built_site / "category/pii.md").is_file()
    html = (built_site / "datatype/email.html").read_text("utf-8")
    assert '<link rel="alternate" type="text/markdown" href="/datatype/email.md"' in html
    draft = (built_site / "datatype/runpa.md").read_text("utf-8")
    assert "> **Draft.**" in draft


def test_rag_corpus_and_manifest(built_site):
    lines = (built_site / "api/v1/rag/corpus.jsonl").read_text("utf-8").splitlines()
    entries = [json.loads(line) for line in lines]
    email = next(e for e in entries if e["id"] == "email")
    assert email["text"].startswith("Name: Email (Electronic mail)\nID: email\n")
    assert email["metadata"]["status"] == "stable"
    manifest = json.loads((built_site / "api/v1/index.json").read_text("utf-8"))
    assert manifest["rag_template_version"] == "1"
    assert "api/v1/rag/corpus.jsonl" in manifest["files"]
    assert manifest["llms_txt"] == "https://registry.apicrafter.io/llms.txt"


def test_skos_export_parses(built_site):
    rdflib = pytest.importorskip("rdflib")
    from rdflib.namespace import RDF, SKOS

    graph = rdflib.Graph()
    graph.parse(built_site / "registry.ttl", format="turtle")
    dt = rdflib.Namespace("https://registry.apicrafter.io/datatype/")
    assert (dt.uspassport, SKOS.broader, dt.passport) in graph
    assert (dt.usssn, SKOS.altLabel, rdflib.Literal("ssn")) in graph
    assert (
        dt.mac_address,
        SKOS.exactMatch,
        rdflib.URIRef("http://www.wikidata.org/entity/P2817"),
    ) in graph
    concepts = set(graph.subjects(RDF.type, SKOS.Concept))
    records = json.loads((built_site / "api/v1/datatypes.json").read_text("utf-8"))
    assert len(concepts) == len(records)


def test_agents_page(built_site):
    html = (built_site / "agents.html").read_text("utf-8")
    assert "identify_values" in html and "claude mcp add metacrafter-registry" in html
    assert (
        (built_site / "agents.md")
        .read_text("utf-8")
        .startswith("# Metacrafter Registry for AI agents")
    )
