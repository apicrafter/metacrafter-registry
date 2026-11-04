from __future__ import annotations

import json
import textwrap

import pytest
from conftest import DATA, write_record

from metacrafter_registry import Registry
from metacrafter_registry.cli import main
from metacrafter_registry.fibo import (
    IRI_BASE,
    load_vocabulary,
    mapped_paths,
    normalize,
    scan_classes,
    search,
)
from metacrafter_registry.loader import load_sources
from metacrafter_registry.validate import validate

IBAN = "FBC/ProductsAndServices/ClientsAndAccounts/InternationalBankAccountIdentifier"
EMAIL = "FND/Places/VirtualPlaces/ElectronicMailAddress"

RDF_HEADER = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE rdf:RDF [
  <!ENTITY fibo-fnd-plc-vrt "https://spec.edmcouncil.org/fibo/ontology/FND/Places/VirtualPlaces/">
  <!ENTITY fibo-fnd-utl-av "https://spec.edmcouncil.org/fibo/ontology/FND/Utilities/AnnotationVocabulary/">
]>
<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
  xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#"
  xmlns:owl="http://www.w3.org/2002/07/owl#"
  xmlns:skos="http://www.w3.org/2004/02/skos/core#"
  xmlns:cmns-av="https://www.omg.org/spec/Commons/AnnotationVocabulary/"
  xmlns:fibo-fnd-utl-av="https://spec.edmcouncil.org/fibo/ontology/FND/Utilities/AnnotationVocabulary/">
"""


@pytest.fixture
def fibo_checkout(tmp_path):
    """Two FIBO-like files: one defines a class, the other only adds an axiom to it."""
    root = tmp_path / "fibo"
    (root / "FND/Places").mkdir(parents=True)
    (root / "FND/Places/VirtualPlaces.rdf").write_text(
        RDF_HEADER
        + textwrap.dedent(
            """
            <owl:Ontology rdf:about="https://spec.edmcouncil.org/fibo/ontology/FND/Places/VirtualPlaces/">
              <fibo-fnd-utl-av:hasMaturityLevel rdf:resource="&fibo-fnd-utl-av;Release"/>
            </owl:Ontology>
            <owl:Class rdf:about="&fibo-fnd-plc-vrt;ElectronicMailAddress">
              <rdfs:label xml:lang="en">electronic mail address</rdfs:label>
              <skos:definition xml:lang="en">virtual address for email</skos:definition>
              <cmns-av:abbreviation>email</cmns-av:abbreviation>
            </owl:Class>
            </rdf:RDF>
            """
        ),
        encoding="utf-8",
    )
    (root / "FND/Places/Other.rdf").write_text(
        RDF_HEADER + '<owl:Class rdf:about="&fibo-fnd-plc-vrt;ElectronicMailAddress"/></rdf:RDF>\n',
        encoding="utf-8",
    )
    return root


def _map_email(data_dir, value):
    write_record(
        data_dir / "datatypes/any/pii/email.yaml",
        f"""
        id: email
        name: Email
        status: stable
        doc: Electronic mail address
        langs: [common]
        categories: [pii]
        is_pii: true
        regexp: '^[^@ ]+@[^@ ]+$'
        examples:
        - value: user@example.com
          description: plain address
        mappings:
          fibo: {value}
        """,
    )


def _messages(data_dir, level="error"):
    result = validate(load_sources(data_dir))
    issues = result.errors if level == "error" else result.warnings
    return [f"{i.id}: {i.message}" for i in issues]


def test_normalize_accepts_path_or_iri():
    assert normalize(IRI_BASE + IBAN) == IBAN
    assert normalize("http://spec.edmcouncil.org/fibo/ontology/" + IBAN) == IBAN
    assert normalize(f" {IBAN} ") == IBAN


def test_scan_classes(fibo_checkout):
    classes = scan_classes(fibo_checkout)
    assert classes == {
        EMAIL: {
            "label": "electronic mail address",
            "definition": "virtual address for email",
            "abbreviations": ["email"],
            "maturity": "Release",
            "source_file": "FND/Places/VirtualPlaces.rdf",
        }
    }
    assert [p for p, _ in search(classes, "Mail address")] == [EMAIL]
    assert search(classes, "bank") == []


def test_full_iri_is_rejected(mini_data):
    _map_email(mini_data, IRI_BASE + EMAIL)
    assert any("schema: mappings.fibo" in m for m in _messages(mini_data))


def test_unknown_class_is_rejected(mini_data):
    _map_email(mini_data, EMAIL)
    assert any(
        m.startswith(f"email: mappings.fibo: '{EMAIL}' is not in") for m in _messages(mini_data)
    )


def test_update_check_and_validate(mini_data, fibo_checkout, capsys):
    _map_email(mini_data, EMAIL)
    args = ["--data-dir", str(mini_data), "fibo"]
    assert main([*args, "update", "--fibo-dir", str(fibo_checkout), "--ref", "abc"]) == 0
    vocabulary = load_vocabulary(mini_data)
    assert vocabulary["source"]["ref"] == "abc"
    assert vocabulary["source"]["license"]["name"] == "MIT"
    assert list(vocabulary["terms"]) == [EMAIL]
    assert _messages(mini_data) == []
    assert main([*args, "check", "--fibo-dir", str(fibo_checkout), "--ref", "abc"]) == 0

    # A mapping FIBO does not define cannot be pinned.
    _map_email(mini_data, "FND/Places/VirtualPlaces/ElectronicMailAdress")
    assert main([*args, "update", "--fibo-dir", str(fibo_checkout)]) == 1
    assert "Not a labelled FIBO class" in capsys.readouterr().out
    assert main([*args, "check", "--fibo-dir", str(fibo_checkout)]) == 1

    # A pinned class that no record maps to is reported.
    write_record(
        mini_data / "datatypes/any/pii/email.yaml",
        "id: email\nname: Email\nstatus: stable\ndoc: Electronic mail address\n"
        "langs: [common]\ncategories: [pii]\nis_pii: true\n",
    )
    assert any("is not mapped by any record" in m for m in _messages(mini_data, "warning"))


def test_repository_mappings_are_pinned():
    vocabulary = load_vocabulary(DATA)
    used = mapped_paths(rec.data for rec in load_sources(DATA).datatypes)
    assert sorted(used) == sorted(vocabulary["terms"])
    assert vocabulary["source"]["repo"] == "edmcouncil/fibo"
    assert len(vocabulary["source"]["ref"]) == 40
    assert {t["maturity"] for t in vocabulary["terms"].values()} == {"Release"}


def test_crosswalk_fibo():
    reg = Registry.from_sources(DATA)
    assert [r["id"] for r in reg.crosswalk("fibo", IBAN)] == ["iban"]
    assert [r["id"] for r in reg.crosswalk("fibo", IRI_BASE + IBAN)] == ["iban"]
    bic = "FBC/FunctionalEntities/FinancialServicesEntities/BusinessIdentifierCode"
    assert sorted(r["id"] for r in reg.crosswalk("fibo", bic)) == ["bic", "swiftcode"]


def test_fibo_in_published_outputs(built_site):
    iri = IRI_BASE + IBAN
    html = (built_site / "datatype/iban.html").read_text("utf-8")
    assert f'href="{iri}"' in html
    assert "international bank account identifier</a> (IBAN)" in html
    jsonld = json.loads(
        html.split('<script type="application/ld+json">', 1)[1].split("</script>")[0]
    )
    assert iri in jsonld["sameAs"]
    assert f"<{iri}>" in (built_site / "datatype/iban.md").read_text("utf-8")
    record = json.loads((built_site / "api/v1/datatypes/iban.json").read_text("utf-8"))
    assert record["mappings"]["fibo"] == IBAN


def test_skos_exact_match_to_fibo(built_site):
    rdflib = pytest.importorskip("rdflib")
    from rdflib.namespace import SKOS

    graph = rdflib.Graph()
    graph.parse(built_site / "registry.ttl", format="turtle")
    dt = rdflib.Namespace("https://registry.apicrafter.io/datatype/")
    assert (dt.iban, SKOS.exactMatch, rdflib.URIRef(IRI_BASE + IBAN)) in graph
