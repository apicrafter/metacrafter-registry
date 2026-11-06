from __future__ import annotations

import json

import yaml
from conftest import write_record

from metacrafter_registry.build import build
from metacrafter_registry.datahub import ROOT_NAME, business_glossary
from metacrafter_registry.fibo import IRI_BASE
from metacrafter_registry.loader import load_sources
from metacrafter_registry.model import build_registry

SITE = "https://registry.example.org"


def _terms(glossary):
    """Yield (dotted name path, term) for every term, as DataHub's ingestion builds paths."""

    def walk(node, path):
        path = path + [node["name"]]
        for term in node.get("terms", []):
            yield ".".join(path + [term["name"]]), term
        for child in node.get("nodes", []):
            yield from walk(child, path)

    for node in glossary["nodes"]:
        yield from walk(node, [])


def test_glossary_on_mini_registry(mini_data):
    reg = build_registry(load_sources(mini_data), SITE)
    glossary = business_glossary(reg, SITE)
    assert glossary["version"] == "1"
    assert glossary["owners"] == {"users": ["datahub"]}
    terms = dict(_terms(glossary))
    assert set(terms) == {f"{ROOT_NAME}.PII.Email", f"{ROOT_NAME}.PII.US email"}

    email = terms[f"{ROOT_NAME}.PII.Email"]
    assert email["id"] == "email"
    assert email["source_ref"] == ROOT_NAME
    assert email["source_url"] == f"{SITE}/datatype/email"
    assert email["custom_properties"]["is_pii"] == "true"
    assert email["custom_properties"]["regexp"] == "^[^@ ]+@[^@ ]+$"
    assert "inherits" not in email

    pattern = terms[f"{ROOT_NAME}.PII.US email"]
    assert pattern["inherits"] == [f"{ROOT_NAME}.PII.Email"]
    assert pattern["custom_properties"]["status"] == "draft"
    assert pattern["custom_properties"]["kind"] == "pattern"


def test_fibo_mapping_is_the_term_source(mini_data):
    path = "FBC/ProductsAndServices/ClientsAndAccounts/InternationalBankAccountIdentifier"
    write_record(
        mini_data / "datatypes/any/pii/iban.yaml",
        f"""
        id: iban
        name: IBAN
        doc: International bank account number
        categories: [pii]
        langs: [common]
        is_pii: false
        mappings:
          fibo: {path}
        """,
    )
    reg = build_registry(load_sources(mini_data), SITE)
    terms = {t["id"]: t for _, t in _terms(business_glossary(reg, SITE))}
    assert terms["iban"]["source_ref"] == "FIBO"
    assert terms["iban"]["source_url"] == IRI_BASE + path
    assert terms["iban"]["custom_properties"]["fibo"] == IRI_BASE + path
    links = [link["url"] for link in terms["iban"]["knowledge_links"]]
    assert links[0] == f"{SITE}/datatype/iban"


def test_clashing_names_get_the_id(mini_data):
    write_record(
        mini_data / "datatypes/any/pii/email2.yaml",
        """
        id: email2
        name: Email
        doc: Another email type
        categories: [pii]
        langs: [common]
        is_pii: true
        """,
    )
    reg = build_registry(load_sources(mini_data), SITE)
    names = {t["id"]: t["name"] for _, t in _terms(business_glossary(reg, SITE))}
    assert names["email"] == "Email (email)"
    assert names["email2"] == "Email (email2)"


def test_published_glossary(built_site):
    text = (built_site / "datahub-glossary.yml").read_text("utf-8")
    glossary = yaml.safe_load(text)
    terms = dict(_terms(glossary))
    ids = [term["id"] for term in terms.values()]
    records = json.loads((built_site / "api/v1/datatypes.json").read_text("utf-8"))

    # One term per record; its id gives the URN that metacrafter attaches.
    assert len(ids) == len(set(ids)) == len(records)
    assert set(ids) == {r["id"] for r in records}
    for path, term in terms.items():
        for target in term.get("inherits", []):
            assert target in terms, f"{path}: unresolved {target}"
        assert all(isinstance(v, str) for v in term["custom_properties"].values())
        assert term["description"]
    by_id = {t["id"]: t for t in terms.values()}
    assert by_id["iban"]["source_ref"] == "FIBO"

    manifest = json.loads((built_site / "api/v1/index.json").read_text("utf-8"))
    assert "datahub-glossary.yml" in manifest["files"]


def test_glossary_is_reproducible(mini_data, tmp_path):
    outputs = []
    for name in ("a", "b"):
        build(mini_data, tmp_path / name, base_url=SITE, update_data_files=False)
        outputs.append((tmp_path / name / "datahub-glossary.yml").read_bytes())
    assert outputs[0] == outputs[1]
