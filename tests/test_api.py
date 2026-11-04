from __future__ import annotations

import csv
import json
import re

import pytest
from jsonschema import Draft202012Validator
from openapi_spec_validator import validate as validate_openapi
from referencing import Registry, Resource

from metacrafter_registry.model import CSV_COLUMNS


def load(site, rel):
    return json.loads((site / rel).read_text("utf-8"))


@pytest.fixture(scope="module")
def spec(built_site):
    return load(built_site, "api/v1/openapi.json")


@pytest.fixture(scope="module")
def schema_validator(spec):
    resource = Resource.from_contents(
        {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "components": spec["components"],
        }
    )
    registry = Registry().with_resource("urn:spec", resource)

    def make(name):
        return Draft202012Validator(
            {"$ref": f"urn:spec#/components/schemas/{name}"}, registry=registry
        )

    return make


def test_openapi_document_is_valid(spec):
    validate_openapi(spec)
    assert "/api/v1/datatypes/{id}.json" in spec["paths"]
    assert "/registry.json" in spec["paths"]


def test_every_record_matches_its_schema(built_site, schema_validator):
    datatype = schema_validator("Datatype")
    errors = [
        f"{r['id']}: {e.message}"
        for r in load(built_site, "api/v1/datatypes.json")
        for e in datatype.iter_errors(r)
    ]
    assert errors == []
    tool = schema_validator("Tool")
    assert [
        e.message for t in load(built_site, "api/v1/tools.json") for e in tool.iter_errors(t)
    ] == []
    manifest = schema_validator("Manifest")
    assert list(manifest.iter_errors(load(built_site, "api/v1/index.json"))) == []
    reference = schema_validator("Reference")
    for name in ("categories", "countries", "languages"):
        assert list(reference.iter_errors(load(built_site, f"api/v1/{name}.json")[0])) == []


def test_v1_record_is_normalized(built_site):
    email = load(built_site, "api/v1/datatypes/email.json")
    assert email["kind"] == "datatype"
    assert email["is_pii"] is True
    assert all(isinstance(c, str) for c in email["categories"])
    # empty source values are omitted, not published as "" or []
    assert "regexp" not in email and "examples" not in email
    assert email["urls"]["html"] == "https://registry.apicrafter.io/datatype/email"
    assert email["source"]["path"].startswith("data/datatypes/")


def test_pattern_links_back(built_site):
    passport = load(built_site, "api/v1/datatypes/passport.json")
    uk = load(built_site, "api/v1/datatypes/ukpassport.json")
    assert "ukpassport" in passport["patterns"]
    assert uk["kind"] == "pattern" and uk["semantic_type"] == "passport"
    assert uk["is_pii"] is True


def test_collections_agree(built_site):
    records = load(built_site, "api/v1/datatypes.json")
    lines = (built_site / "api/v1/datatypes.jsonl").read_text("utf-8").splitlines()
    assert [json.loads(line) for line in lines] == records
    with open(built_site / "api/v1/datatypes.csv", encoding="utf-8", newline="") as handle:
        rows = list(csv.reader(handle))
    assert rows[0] == CSV_COLUMNS
    assert len(rows) - 1 == len(records)
    legacy = load(built_site, "registry.json")
    aliases = load(built_site, "api/v1/aliases.json")
    # legacy registry.json also keeps retired ids (aliases) as entries
    assert {r["id"] for r in records} | set(aliases) == set(legacy)


def test_reference_counts(built_site):
    records = load(built_site, "api/v1/datatypes.json")
    categories = {c["id"]: c for c in load(built_site, "api/v1/categories.json")}
    expected = sum(1 for r in records if "pii" in r.get("categories", []))
    assert categories["pii"]["count"] == expected


def test_manifest_hashes_cover_bulk_files(built_site):
    manifest = load(built_site, "api/v1/index.json")
    for name in ("registry.json", "api/v1/datatypes.json", "api/v1/datatypes.csv"):
        assert name in manifest["files"]
    assert manifest["license"] == "Apache-2.0"
    records = load(built_site, "api/v1/datatypes.json")
    assert manifest["counts"]["datatypes"] + manifest["counts"]["patterns"] == len(records)


def test_search_index(built_site):
    index = load(built_site, "search-index.json")
    email = next(e for e in index if e["id"] == "email")
    assert "почта" in email["t"].lower()
    assert len(index) == len(load(built_site, "api/v1/datatypes.json"))


def test_entity_page_structured_data(built_site):
    html = (built_site / "datatype/email.html").read_text("utf-8")
    match = re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
    assert match
    data = json.loads(match.group(1))
    assert data["@type"] == "DefinedTerm"
    assert data["termCode"] == "email"
    assert "https://schema.org/email" in data["sameAs"]
    assert '<link rel="canonical" href="https://registry.apicrafter.io/datatype/email">' in html


def test_sitemap_lists_entity_pages(built_site):
    sitemap = (built_site / "sitemap.xml").read_text("utf-8")
    assert "<loc>https://registry.apicrafter.io/datatype/email</loc>" in sitemap
    assert "<loc>https://registry.apicrafter.io/category/pii</loc>" in sitemap
    robots = (built_site / "robots.txt").read_text("utf-8")
    assert "Sitemap: https://registry.apicrafter.io/sitemap.xml" in robots


def test_aliases(built_site):
    aliases = load(built_site, "api/v1/aliases.json")
    assert aliases["ssn"] == "usssn" and aliases["eui48"] == "mac_address"
    assert list(aliases) == sorted(aliases)
    usssn = load(built_site, "api/v1/datatypes/usssn.json")
    assert "ssn" in usssn["aliases"]
    legacy = load(built_site, "datatype/ssn.json")
    assert legacy["alias_of"] == "usssn"
    page = (built_site / "datatype/ssn.html").read_text("utf-8")
    assert 'http-equiv="refresh" content="0; url=/datatype/usssn"' in page
    assert '<link rel="canonical" href="https://registry.apicrafter.io/datatype/usssn">' in page
    assert "/datatype/ssn<" not in (built_site / "sitemap.xml").read_text("utf-8")


def test_status_and_quality_published(built_site):
    records = load(built_site, "api/v1/datatypes.json")
    statuses = {r["status"] for r in records}
    assert statuses <= {"draft", "stable", "deprecated"} and "draft" in statuses
    assert all(0 <= r["quality"]["score"] <= 100 for r in records)
    manifest = load(built_site, "api/v1/index.json")
    assert manifest["counts"]["draft"] == sum(r["status"] == "draft" for r in records)
    draft = next(r for r in records if r["status"] == "draft")
    html = (built_site / f"datatype/{draft['id']}.html").read_text("utf-8")
    assert "has not been reviewed yet" in html


def test_schemas_published(built_site):
    for name in ("datatype", "pattern", "tool"):
        schema = load(built_site, f"schema/{name}.schema.json")
        assert schema["$id"] == f"https://registry.apicrafter.io/schema/{name}.schema.json"
