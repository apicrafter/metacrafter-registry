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


def test_cdm_crosswalk(repo_sources):
    from metacrafter_registry import Registry

    reg = Registry.from_sources(DATA)
    assert [r["id"] for r in reg.crosswalk("cdm", "means.identity.service.email")] == ["email"]
    assert [r["id"] for r in reg.crosswalk("cdm", "means.location.postalCode")] == ["postindex"]
    # a pattern can carry the mapping, and a record can list several traits
    assert [r["id"] for r in reg.crosswalk("cdm", "means.measurement.currency.iSOCode")] == [
        "iso4217curcode"
    ]
    # every CDM trait maps to at most one registry record
    seen: dict[str, str] = {}
    for record in reg.datatypes.values():
        value = record.get("mappings", {}).get("cdm")
        for trait in value if isinstance(value, list) else [value] if value else []:
            assert trait not in seen, f"{trait} is mapped by {seen[trait]} and {record['id']}"
            seen[trait] = record["id"]
    assert len(seen) >= 40


def test_cdm_mapping_must_be_a_trait_name(mini_data):
    path = mini_data / "datatypes/any/pii/email.yaml"
    path.write_text(path.read_text() + "mappings:\n  cdm: email\n")
    errors = [str(i) for i in validate(load_sources(mini_data)).errors]
    assert any("mappings" in e and "cdm" in e for e in errors), errors

    path.write_text(path.read_text().replace("cdm: email", "cdm: means.identity.service.email"))
    assert validate(load_sources(mini_data)).errors == []


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


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")
def test_javascript_checksums_match_python(tmp_path):
    """Every check-digit algorithm exists in identify-core.js and gives the same answers."""
    import random

    from metacrafter_registry.checksums import ALGORITHMS

    rng = random.Random(3)
    values = [
        "4111 1111 1111 1111",
        "GB82 WEST 1234 5698 7654 32",
        "978-0-521-29366-2",
        "0-521-22151-X",
        "7707083893",
        "112-233-445 95",
        "2 95 10 99 126 111 93",
        "253072B07300470",
        "253072A07300443",
        "ATU13585627",
        "U13585626",
        "BG175074752",
        "BG 175 074 751",
        "151086 95088",
        "RCCMNL83S18D969H",
        "CNTCHR83T41D969D",
        "IT 00743110157",
        "131052-308T",
        "131052A308T",
        "54362315-K",
    ]
    values += [str(rng.randrange(10**8, 10**15)) for _ in range(300)]
    values += [f"ATU{rng.randrange(10**8):08d}" for _ in range(100)]
    values += [f"BG{rng.randrange(10**10):010d}" for _ in range(100)]
    values += [
        f"{rng.randrange(10**5):05d}2{rng.choice('AB')}{rng.randrange(10**8):08d}"
        for _ in range(100)
    ]
    values += [f"{rng.randrange(10**11):011d}" for _ in range(1000)]
    offices = ["001", "100", "121", "888", "500"]
    values += [
        f"IT{rng.randrange(10**7):07d}{rng.choice(offices)}{rng.randrange(10)}" for _ in range(100)
    ]
    values += [
        f"{rng.randrange(10**6):06d}{rng.choice('-+ABCDEFUVWXY')}{rng.randrange(1000):03d}"
        f"{rng.choice('0123456789ABCDEFHJKLMNPRSTUVWXY')}"
        for _ in range(200)
    ]
    values += [
        f"{rng.randrange(10**8):08d}{rng.choice('TRWAGMYFPDXBNJZSQVHLCKE')}" for _ in range(200)
    ]
    letters, digits = "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "0123456789LMNPQRSTUV"
    fiscal_code = [letters] * 6 + [digits] * 2 + ["ABCDEHLMPRST"] + [digits] * 2
    fiscal_code += [letters] + [digits] * 3 + [letters]
    values += ["".join(rng.choice(chars) for chars in fiscal_code) for _ in range(500)]
    script = tmp_path / "checksums.js"
    script.write_text(
        "const core = require(process.argv[2]);\n"
        "const names = JSON.parse(process.argv[3]);\n"
        "const values = JSON.parse(process.argv[4]);\n"
        "console.log(JSON.stringify(names.map(n => core.CHECKSUMS[n] ? "
        "values.map(v => core.CHECKSUMS[n](v)) : null)));\n"
    )
    names = sorted(ALGORITHMS)
    out = subprocess.run(
        [
            "node",
            str(script),
            str(REPO / "src/metacrafter_registry/static/identify-core.js"),
            json.dumps(names),
            json.dumps(values),
        ],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    for name, js in zip(names, json.loads(out), strict=True):
        assert js is not None, f"{name} is missing from identify-core.js"
        assert js == [ALGORITHMS[name](v) for v in values], name
