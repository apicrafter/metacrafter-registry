from __future__ import annotations

import yaml
from conftest import DATA, write_record

from metacrafter_registry.loader import load_sources
from metacrafter_registry.migrate import (
    apply_migration,
    is_stub,
    migrate_datatype,
    migrate_tool,
    plan_migration,
    plan_reference_lists,
)
from metacrafter_registry.quality import score_record
from metacrafter_registry.validate import validate

V1_RECORD = {
    "categories": ["pii"],
    "doc": "  Russian taxpayer number issued to organizations and individuals  ",
    "id": "inn",
    "is_pii": "True",
    "langs": ["ru"],
    "links": [{"type": "wikipedia", "url": "https://ru.wikipedia.org/wiki/ИНН"}, {"type": "other"}],
    "name": "INN",
    "regexp": "",
    "wikidata_property": "P1234",
    "parent": {"type": "taxid"},
    "patterns": ["ruinn10"],
    "translations": {"ru": "ИНН", "en": {"name": "", "doc": ""}},
    "examples": [
        {"value": 7707083893, "description": " Sberbank "},
        {"value": "", "description": ""},
    ],
    "classification": "identifier",
}


def test_migrate_datatype_v1_to_v2():
    out = migrate_datatype(V1_RECORD, None)
    assert list(out) == [
        "id",
        "name",
        "status",
        "doc",
        "parent",
        "categories",
        "langs",
        "is_pii",
        "classification",
        "examples",
        "mappings",
        "links",
        "translations",
    ]
    assert out["is_pii"] is True
    assert out["parent"] == "taxid"
    assert out["mappings"] == {"wikidata": "P1234"}
    assert "regexp" not in out and "patterns" not in out and "wikidata_property" not in out
    assert out["translations"] == {"ru": {"name": "ИНН"}}
    assert out["examples"] == [{"value": "7707083893", "description": "Sberbank"}]
    assert out["links"] == [{"type": "wikipedia", "url": "https://ru.wikipedia.org/wiki/ИНН"}]
    assert out["doc"].startswith("Russian")
    assert out["status"] == "stable"


def test_migrate_is_idempotent_on_records():
    once = migrate_datatype(V1_RECORD, None)
    assert migrate_datatype(once, None) == once


def test_pattern_drops_inherited_fields():
    parent = {"id": "passport", "is_pii": "True", "categories": ["pii", "persons"]}
    pattern = {
        "id": "ukpassport",
        "name": "UK passport",
        "doc": "Number of the passport issued by the United Kingdom",
        "semantic_type": "passport",
        "is_pii": "True",
        "categories": ["persons", "pii"],
        "langs": ["en"],
        "links": [{"type": "wikipedia", "url": "https://en.wikipedia.org/wiki/British_passport"}],
    }
    out = migrate_datatype(pattern, parent)
    assert "is_pii" not in out and "categories" not in out
    narrower = migrate_datatype({**pattern, "categories": ["persons"]}, parent)
    assert narrower["categories"] == ["persons"]  # an override is kept


def test_stub_detection():
    assert is_stub({"name": "Hash", "doc": "Hash"})
    assert is_stub({"name": "X", "doc": "Too short"})
    assert is_stub({"name": "X", "doc": "A long enough description of a thing"})  # no evidence
    assert not is_stub(
        {"name": "X", "doc": "A long enough description of a thing", "regexp": "^x$"}
    )


def test_migrate_tool_dedupes_supported_types():
    out = migrate_tool(
        {
            "id": "t",
            "name": "T",
            "category": "other",
            "doc": "d",
            "supported_types": ["a", "b", "a"],
            "website": "",
        }
    )
    assert out == {
        "id": "t",
        "name": "T",
        "category": "other",
        "doc": "d",
        "supported_types": ["a", "b"],
    }


def test_repository_is_fully_migrated():
    plan = plan_migration(DATA)
    assert plan.changed == [], plan.changed[:5]
    assert plan_reference_lists(DATA) == {}


def test_migration_end_to_end(tmp_path, mini_data):
    write_record(
        mini_data / "datatypes/any/pii/old_name.yaml",
        """
        id: legacything
        name: Legacy thing
        doc: A record written in the release 1.02 style
        langs: [en]
        is_pii: 'False'
        regexp: ''
        wikidata_property: ''
        examples: []
        """,
    )
    plan = plan_migration(mini_data)
    apply_migration(mini_data, plan, plan_reference_lists(mini_data))
    migrated = mini_data / "datatypes/any/pii/legacything.yaml"
    assert migrated.exists() and not (mini_data / "datatypes/any/pii/old_name.yaml").exists()
    data = yaml.safe_load(migrated.read_text())
    assert data["is_pii"] is False and data["status"] == "draft"
    assert validate(load_sources(mini_data)).errors == []
    assert plan_migration(mini_data).changed == []
    langs = yaml.safe_load((mini_data / "langs.yaml").read_text())
    assert {e["id"]: e["kind"] for e in langs} == {"en": "language", "common": "special"}


def test_schema_rejects_v1_conventions(mini_data):
    write_record(
        mini_data / "datatypes/any/pii/v1style.yaml",
        """
        id: v1style
        name: Old style
        status: stable
        doc: Written with release 1.02 conventions
        langs: [en]
        is_pii: 'True'
        regexp: ''
        mappings:
          wikidata: https://www.wikidata.org/wiki/Property:P968
        """,
    )
    errors = [str(e) for e in validate(load_sources(mini_data)).errors]
    assert any("is_pii: 'True' is not of type 'boolean'" in e for e in errors), errors
    assert any("regexp: '' should be non-empty" in e for e in errors), errors
    assert any("mappings.wikidata" in e for e in errors), errors


def test_quality_score_rubric():
    full = {
        "name": "IBAN",
        "doc": "International Bank Account Number, an internationally agreed system of identifying "
        "bank accounts across national borders",
        "regexp": "^[A-Z]{2}\\d{2}[A-Z0-9]{11,30}$",
        "examples": [
            {"value": "a", "valid": True},
            {"value": "b", "valid": True},
            {"value": "c", "valid": False},
        ],
        "links": [{"type": "wikipedia", "url": "https://x"}],
        "mappings": {"wikidata": "P1"},
        "translations": {"ru": {"name": "x"}},
        "detected_by": {"tools": ["presidio"]},
    }
    assert score_record(full) == {"score": 100, "missing": []}
    stub = score_record({"name": "Hash", "doc": "Hash"})
    assert stub["score"] == 0
    assert "description" in stub["missing"] and "regexp" in stub["missing"]


def test_is_pii_spellings():
    from metacrafter_registry.migrate import _as_bool

    assert [_as_bool(v) for v in ("True", "true", "YES", "1", True)] == [True] * 5
    assert [_as_bool(v) for v in ("False", "false", "no", "0", False)] == [False] * 5
    assert _as_bool("") is None and _as_bool(None) is None
    assert _as_bool("maybe") == "maybe"  # left for validation to reject
