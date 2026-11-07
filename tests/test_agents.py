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
    assert "## Email address" in full and "id `email`" in full


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
    assert email["text"].startswith("Name: Email address\nID: email\n")
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
        dt.isrc,
        SKOS.exactMatch,
        rdflib.URIRef("http://www.wikidata.org/entity/P1243"),
    ) in graph
    concepts = set(graph.subjects(RDF.type, SKOS.Concept))
    records = json.loads((built_site / "api/v1/datatypes.json").read_text("utf-8"))
    assert len(concepts) == len(records)


SITE = "https://registry.apicrafter.io"


def _turtle(path):
    rdflib = pytest.importorskip("rdflib")
    graph = rdflib.Graph()
    graph.parse(path, format="turtle")
    return graph


def _records(built_site) -> dict:
    records = json.loads((built_site / "api/v1/datatypes.json").read_text("utf-8"))
    return {r["id"]: r for r in records}


def _values(record: dict, key: str) -> list:
    value = record.get("mappings", {}).get(key)
    return value if isinstance(value, list) else [value] if value else []


def test_rdf_mapping_links(built_site):
    rdflib = pytest.importorskip("rdflib")
    from rdflib.namespace import SKOS

    graph = _turtle(built_site / "registry.ttl")
    records = _records(built_site)
    dt = rdflib.Namespace(f"{SITE}/datatype/")
    official_id = rdflib.URIRef("https://w3id.org/dpv/pd#OfficialID")
    assert (dt.usssn, SKOS.broadMatch, official_id) in graph
    assert (dt.usssn, SKOS.exactMatch, official_id) not in graph
    fhir = rdflib.URIRef("http://hl7.org/fhir/sid/us-ssn")
    assert (dt.usssn, SKOS.exactMatch, fhir) in graph
    # Every DPV value becomes a broadMatch; none is dropped.
    dpv = {(rid, v) for rid, r in records.items() for v in _values(r, "dpv")}
    assert len(dpv) == len(list(graph.subject_objects(SKOS.broadMatch)))
    bio_id, bio = next((rid, r) for rid, r in records.items() if _values(r, "bioregistry"))
    for prefix in _values(bio, "bioregistry"):
        iri = rdflib.URIRef(f"https://bioregistry.io/registry/{prefix}")
        assert (dt[bio_id], SKOS.exactMatch, iri) in graph
    d3m = [
        (rid, v)
        for rid, r in records.items()
        for v in _values(r, "d3m")
        if v.startswith("http://schema.org/")
    ]
    assert d3m
    for rid, value in d3m:
        https = value.replace("http://", "https://", 1)
        assert (dt[rid], SKOS.exactMatch, rdflib.URIRef(https)) in graph
        assert (dt[rid], SKOS.exactMatch, rdflib.URIRef(value)) not in graph


def test_rdf_detection_payload(built_site):
    rdflib = pytest.importorskip("rdflib")
    from rdflib.namespace import DCTERMS, RDFS, SKOS

    graph = _turtle(built_site / "registry.ttl")
    email = _records(built_site)["email"]
    dt = rdflib.Namespace(f"{SITE}/datatype/")
    mcr = rdflib.Namespace(f"{SITE}/vocab#")
    assert (dt.email, mcr.regexp, rdflib.Literal(email["regexp"])) in graph
    assert (dt.email, mcr.status, rdflib.Literal("stable")) in graph
    assert (dt.email, mcr.isPII, rdflib.Literal(True)) in graph
    examples = set(graph.objects(dt.email, SKOS.example))
    valid = {rdflib.Literal(e["value"]) for e in email["examples"] if e.get("valid", True)}
    invalid = {rdflib.Literal(e["value"]) for e in email["examples"] if not e.get("valid", True)}
    assert examples == valid and valid and not examples & invalid
    for link in email["links"]:
        assert (dt.email, RDFS.seeAlso, rdflib.URIRef(link["url"])) in graph
    assert (dt.usssn, DCTERMS.spatial, rdflib.URIRef(f"{SITE}/country/US")) in graph
    english = rdflib.URIRef("http://id.loc.gov/vocabulary/iso639-1/en")
    assert (dt.usssn, DCTERMS.language, english) in graph
    assert not any(str(o).endswith("/common") for o in graph.objects(None, DCTERMS.language))


def test_rdf_top_concepts_and_tools(built_site):
    rdflib = pytest.importorskip("rdflib")
    from rdflib.namespace import RDF, SKOS

    graph = _turtle(built_site / "registry.ttl")
    dt = rdflib.Namespace(f"{SITE}/datatype/")
    mcr = rdflib.Namespace(f"{SITE}/vocab#")
    tops = set(graph.subjects(SKOS.topConceptOf, rdflib.URIRef(f"{SITE}/")))
    assert tops == set(graph.objects(rdflib.URIRef(f"{SITE}/"), SKOS.hasTopConcept))
    assert dt.uspassport not in tops and dt.email in tops
    assert not [t for t in tops if (t, SKOS.broader, None) in graph]
    concepts = set(graph.subjects(RDF.type, SKOS.Concept))
    without_broader = {c for c in concepts if (c, SKOS.broader, None) not in graph}
    assert tops == without_broader
    presidio = rdflib.URIRef(f"{SITE}/tool/presidio")
    assert (presidio, RDF.type, mcr.Tool) in graph
    assert (presidio, mcr.supportedType, dt.email) in graph
    assert set(graph.objects(None, mcr.supportedType)) <= concepts


def test_rdf_tool_resolves_alias():
    from metacrafter_registry.agents import skos_turtle

    record = {
        "id": "usssn",
        "name": "US SSN",
        "doc": "Social Security number.",
        "status": "stable",
        "is_pii": True,
        "aliases": ["ssn"],
    }
    tool = {"id": "scanner", "name": "Scanner", "supported_types": ["ssn", "unknown"]}
    text = skos_turtle([record], [], SITE, "1", [tool])
    assert "tool:scanner a mcr:Tool" in text
    assert "mcr:supportedType dt:usssn" in text and "dt:unknown" not in text


def test_rdf_url_escaping():
    from metacrafter_registry.agents import _ttl_url

    assert _ttl_url("https://example.org/a b|c") == "<https://example.org/a%20b%7Cc>"


def test_rdf_vocabulary(built_site):
    rdflib = pytest.importorskip("rdflib")
    from rdflib.namespace import OWL, RDF, RDFS

    vocab = _turtle(built_site / "vocab.ttl")
    graph = _turtle(built_site / "registry.ttl")
    mcr = f"{SITE}/vocab#"
    assert (rdflib.URIRef(f"{SITE}/vocab"), RDF.type, OWL.Ontology) in vocab
    used = {p for _, p, _ in graph if str(p).startswith(mcr)}
    used |= {o for o in graph.objects(None, RDF.type) if str(o).startswith(mcr)}
    declared = {s for s in vocab.subjects(RDFS.comment, None) if str(s).startswith(mcr)}
    assert used and used <= declared
    html = (built_site / "vocab.html").read_text("utf-8")
    for term in declared:
        assert f'id="{term[len(mcr) :]}"' in html


def test_rdf_record_files(built_site):
    rdflib = pytest.importorskip("rdflib")

    graph = _turtle(built_site / "registry.ttl")
    dt = rdflib.Namespace(f"{SITE}/datatype/")
    email = _turtle(built_site / "datatype/email.ttl")
    assert set(email.triples((dt.email, None, None))) == set(graph.triples((dt.email, None, None)))
    alias = _turtle(built_site / "datatype/ssn.ttl")
    assert set(alias.subjects()) == {dt.usssn}
    html = (built_site / "datatype/email.html").read_text("utf-8")
    assert '<link rel="alternate" type="text/turtle" href="/datatype/email.ttl"' in html
    manifest = json.loads((built_site / "api/v1/index.json").read_text("utf-8"))
    assert "vocab.ttl" in manifest["files"]


def test_agents_page(built_site):
    html = (built_site / "agents.html").read_text("utf-8")
    assert "identify_values" in html and "claude mcp add metacrafter-registry" in html
    assert (
        (built_site / "agents.md")
        .read_text("utf-8")
        .startswith("# Metacrafter Registry for AI agents")
    )


def test_js_regexp_anchors():
    from metacrafter_registry.agents import js_regexp

    assert js_regexp(r"\A\d+\Z") == (r"^\d+$", "")
    assert js_regexp(r"^\\A$") == (r"^\\A$", "")  # an escaped backslash, then A
