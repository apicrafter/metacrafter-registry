from __future__ import annotations

import json
import shutil
import subprocess

import pytest
from conftest import DATA, REPO, write_record

from metacrafter_registry.changes import diff_records
from metacrafter_registry.coverage import (
    build_coverage,
    coverage_report,
    effective_supported_types,
    load_coverage,
    read_lock,
)
from metacrafter_registry.loader import load_sources
from metacrafter_registry.validate import validate


def test_committed_coverage_matches_the_lock():
    coverage = load_coverage(DATA)
    lock = read_lock(DATA)["metacrafter-rules"]
    assert coverage["source"]["ref"] == lock["ref"]
    assert lock["repo"] == "apicrafter/metacrafter-rules"
    assert len(coverage["rules"]) > 1000


def test_rule_coverage_on_records(built_site):
    email = json.loads((built_site / "api/v1/datatypes/email.json").read_text("utf-8"))
    rules = email["detected_by"]["metacrafter_rules"]
    assert rules and {"rule", "type", "match", "file"} <= set(rules[0])
    report = json.loads((built_site / "api/v1/coverage.json").read_text("utf-8"))
    assert report["datatypes_with_rules"] > 400
    assert "email" not in report["datatypes_without_rules"]


def test_metacrafter_tool_types_are_generated(repo_sources):
    types = effective_supported_types(repo_sources)["metacrafter"]
    covered = coverage_report(load_coverage(DATA), {r.id for r in repo_sources.datatypes}, {})[
        "datatypes_with_rules"
    ]
    assert len(types) == covered or len(types) >= covered - 10
    assert "email" in types


def test_coverage_scan_and_alias_resolution(mini_data, tmp_path):
    rules = tmp_path / "rules" / "common"
    rules.mkdir(parents=True)
    (rules / "common.yaml").write_text(
        "name: c\ncontext: common\nrules:\n"
        "  emailbyname:\n    key: email\n    type: field\n    match: text\n"
        "  oldkey:\n    key: e_mail\n    type: data\n    match: ppr\n"
        "  orphan:\n    key: nothing_here\n    type: field\n    match: text\n"
    )
    coverage = build_coverage(tmp_path / "rules", "0" * 40)
    report = coverage_report(coverage, {"email", "usemail"}, {"e_mail": "email"})
    assert report["orphan_rule_keys"] == {"nothing_here": ["common/common.yaml#orphan"]}
    assert report["datatypes_with_rules"] == 1
    assert report["datatypes_without_rules"] == ["usemail"]


def test_lock_mismatch_is_an_error(mini_data):
    (mini_data / "coverage").mkdir()
    (mini_data / "coverage" / "metacrafter-rules.json").write_text(
        json.dumps({"source": {"repo": "x", "ref": "a" * 40}, "rules": []})
    )
    (mini_data.parent / "ecosystem.lock").write_text(
        "metacrafter-rules:\n  repo: x\n  ref: " + "b" * 40 + "\n"
    )
    errors = [str(i) for i in validate(load_sources(mini_data)).errors]
    assert any("ecosystem.lock pins" in e for e in errors), errors


def test_regexp_matching_empty_string_is_rejected(mini_data):
    write_record(
        mini_data / "datatypes/any/pii/loose.yaml",
        "id: loose\nname: Loose\nstatus: stable\ndoc: Loose\nlangs: [en]\nis_pii: false\n"
        "regexp: '[A-Z]+|'\n",
    )
    errors = [str(i) for i in validate(load_sources(mini_data)).errors]
    assert any("regexp matches an empty string" in e for e in errors)


def test_crosswalk_mappings(repo_sources):
    from metacrafter_registry import Registry

    reg = Registry.from_sources(DATA)
    assert [r["id"] for r in reg.crosswalk("presidio", "US_SSN")] == ["usssn"]
    assert "iban" in [r["id"] for r in reg.crosswalk("google_dlp", "IBAN_CODE")]
    assert "uknino" in [
        r["id"] for r in reg.crosswalk("purview", "U.K. national insurance number (NINO)")
    ]


def test_changes_diff():
    old = [
        {"id": "a", "status": "draft", "name": "A"},
        {"id": "b", "status": "stable", "name": "B"},
        {"id": "dup", "status": "draft", "name": "Dup"},
    ]
    new = [
        {"id": "a", "status": "stable", "name": "A2", "quality": {"score": 1}},
        {"id": "b", "status": "stable", "name": "B", "aliases": ["dup"]},
        {"id": "c", "status": "draft", "name": "C"},
    ]
    diff = diff_records(old, new, "v1", "v2")
    assert diff["added"] == ["c"]
    assert diff["merged"] == {"dup": "b"}
    assert diff["removed"] == []
    assert diff["status_changed"] == [{"id": "a", "from": "draft", "to": "stable"}]
    assert {"id": "a", "fields": ["name"]} in diff["changed"]


def test_quality_identify_and_changes_pages(built_site):
    assert "Drafts to review" in (built_site / "quality.html").read_text("utf-8")
    assert "No release has been published" in (built_site / "changes.html").read_text("utf-8")
    assert json.loads((built_site / "api/v1/changes.json").read_text("utf-8")) == []
    page = (built_site / "identify.html").read_text("utf-8")
    assert "Your values stay in this browser tab" in page
    for asset in ("identify.js", "identify-core.js", "identify-worker.js"):
        assert (built_site / "assets" / asset).is_file()


def test_identify_page_sends_no_values():
    """The only network request of the identify scripts is the index download."""
    static = REPO / "src" / "metacrafter_registry" / "static"
    code = "".join(
        (static / name).read_text("utf-8")
        for name in ("identify.js", "identify-core.js", "identify-worker.js")
    )
    for forbidden in ("XMLHttpRequest", "sendBeacon", "WebSocket", "EventSource", "navigator.send"):
        assert forbidden not in code
    assert code.count("fetch(") == 1 and 'fetch(base + "/identify-index.json")' in code


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")
def test_javascript_identify_matches_python(built_site, tmp_path):
    """The browser scorer and Registry.identify rank the same top candidates."""
    from metacrafter_registry import Registry

    reg = Registry.from_sources(DATA)
    cases = [
        (["7707083893", "7728168971"], "inn"),
        (["GB82 WEST 1234 5698 7654 32", "DE89370400440532013000"], ""),
        (["4111 1111 1111 1111"], "card"),
        (["user@example.com", "first.last+tag@mail.example.org"], ""),
        (["e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"], "sha256"),
    ]
    script = tmp_path / "run.js"
    script.write_text(
        "const core = require(process.argv[2]);\n"
        "const index = require(process.argv[3]);\n"
        "const cases = JSON.parse(process.argv[4]);\n"
        "console.log(JSON.stringify(cases.map(([v, f]) => "
        "core.identify(index, v, f, null, 3).map(r => [r.id, r.score]))));\n"
    )
    out = subprocess.run(
        [
            "node",
            str(script),
            str(REPO / "src/metacrafter_registry/static/identify-core.js"),
            str(built_site / "identify-index.json"),
            json.dumps(cases),
        ],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    js = json.loads(out)
    for (values, field), js_top in zip(cases, js, strict=True):
        py_top = [[r["id"], r["score"]] for r in reg.identify(values, field_name=field, limit=3)]
        assert js_top[0] == py_top[0], (values, js_top, py_top)
