from __future__ import annotations

import json

from conftest import DATA

from metacrafter_registry import legacy


def test_legacy_record_shape(repo_sources):
    records = legacy.build_datatypes(repo_sources)
    email = records["email"]
    assert email["type"] == "datatype"
    assert isinstance(email["is_pii"], bool)
    for field in ("categories", "langs"):
        assert all(set(item) == {"id", "name"} for item in email[field])
    assert list(records) == sorted(records)


def test_patterns_embedded_and_resolved(repo_sources):
    records = legacy.build_datatypes(repo_sources)
    passport = records["passport"]
    embedded = {p["id"]: p for p in passport["patterns"]}
    assert "ukpassport" in embedded
    assert embedded["ukpassport"] == records["ukpassport"]
    assert embedded["ukpassport"]["type"] == "pattern"
    assert all(isinstance(c, dict) for c in embedded["ukpassport"]["categories"])


def test_pattern_is_pii_follows_parent(repo_sources):
    records = legacy.build_datatypes(repo_sources)
    # passport is PII, so its patterns must be too (the old builder got this wrong)
    assert records["passport"]["is_pii"] is True
    assert records["ukpassport"]["is_pii"] is True


def test_tools_have_num(repo_sources):
    tools = legacy.build_tools(repo_sources)
    assert tools["presidio"]["num"] == len(tools["presidio"]["supported_types"])


def test_committed_data_files_are_fresh(repo_sources):
    """data/*_latest.* must equal a fresh build (run `metacrafter-registry build`)."""
    datatypes = json.loads(json.dumps(legacy.build_datatypes(repo_sources), default=str))
    tools = json.loads(json.dumps(legacy.build_tools(repo_sources), default=str))
    assert json.loads((DATA / "datatypes_latest.json").read_text("utf-8")) == datatypes
    assert json.loads((DATA / "tools_latest.json").read_text("utf-8")) == tools
    lines = (DATA / "datatypes_latest.jsonl").read_text("utf-8").splitlines()
    assert {json.loads(line)["id"]: json.loads(line) for line in lines} == datatypes


def test_retired_ids_resolve_in_legacy_output(repo_sources):
    """Merged duplicates keep their old id in registry.json and the JSONL (metacrafter rules)."""
    records = legacy.build_datatypes(repo_sources)
    for alias, canonical in (("ssn", "usssn"), ("ninumber", "uknino"), ("guid", "uuid")):
        entry = records[alias]
        assert entry["id"] == alias and entry["alias_of"] == canonical
        assert entry["name"] == records[canonical]["name"]
