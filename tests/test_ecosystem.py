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


def test_purview_crosswalk(repo_sources):
    from metacrafter_registry import Registry

    reg = Registry.from_sources(DATA)

    def ids(name: str) -> list[str]:
        return [r["id"] for r in reg.crosswalk("purview", name)]

    # case, periods and apostrophes do not matter
    assert ids("U.S. driver's license number") == ["usdriverlic"]
    assert ids("u.s. drivers license number") == ["usdriverlic"]
    # former names keep resolving after Microsoft renamed a type
    assert ids("Azure AD client secret") == ids("Microsoft Entra client secret") == ["api_key"]
    # a bundle resolves to the records of its member types
    eu_passports = ids("EU passport number")
    assert {"at_passport", "frpassport", "plpassport", "uspassport"} <= set(eu_passports)
    assert "github_token" in ids("All credentials")
    assert ids("Germany physical addresses") == ["address"]


def test_purview_tool_lists_every_mapped_record(repo_sources):
    from metacrafter_registry import Registry

    reg = Registry.from_sources(DATA)
    mapped = {rid for rid, r in reg.datatypes.items() if r.get("mappings", {}).get("purview")}
    assert set(reg.tools["microsoftpurview"]["supported_types"]) == mapped
    assert len(mapped) > 200


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


def test_d3m_crosswalk(repo_sources):
    from metacrafter_registry import Registry

    reg = Registry.from_sources(DATA)

    def ids(external_id: str) -> list[str]:
        return [r["id"] for r in reg.crosswalk("d3m", external_id)]

    assert ids("http://schema.org/email") == ["email"]
    # D3M defines schema.org postalCode as a US postal code; a pattern carries it
    assert ids("http://schema.org/postalCode") == ["uszipcode"]
    assert ids("https://metadata.datadrivendiscovery.org/types/FileName") == ["filename"]
    assert ids("https://metadata.datadrivendiscovery.org/types/AmericanPhoneNumber") == [
        "nanpphone"
    ]
    # https schema.org URIs and bare type names resolve too
    assert ids("https://schema.org/email") == ["email"]
    assert ids("FileName") == ["filename"]
    assert ids("addressCountry") == ["country"]
    # column roles are not value types and are not mapped
    assert ids("https://metadata.datadrivendiscovery.org/types/PrimaryKey") == []
    # every D3M semantic type maps to at most one registry record
    seen: dict[str, str] = {}
    for record in reg.datatypes.values():
        value = record.get("mappings", {}).get("d3m")
        for uri in value if isinstance(value, list) else [value] if value else []:
            assert uri not in seen, f"{uri} is mapped by {seen[uri]} and {record['id']}"
            seen[uri] = record["id"]
    assert len(seen) >= 13


def test_d3m_mapping_must_be_a_semantic_type_uri(mini_data):
    path = mini_data / "datatypes/any/pii/email.yaml"
    path.write_text(path.read_text() + "mappings:\n  d3m: email\n")
    errors = [str(i) for i in validate(load_sources(mini_data)).errors]
    assert any("mappings" in e and "d3m" in e for e in errors), errors

    path.write_text(path.read_text().replace("d3m: email", "d3m: http://schema.org/email"))
    assert validate(load_sources(mini_data)).errors == []


def test_fta_crosswalk(repo_sources):
    from metacrafter_registry import Registry

    reg = Registry.from_sources(DATA)

    def ids(name: str) -> list[str]:
        return [r["id"] for r in reg.crosswalk("fta", name)]

    assert ids("EMAIL") == ["email"]
    assert ids("POSTAL_CODE.ZIP5_US") == ["uszipcode"]
    assert ids("POSTAL_CODE.POSTAL_CODE_CA") == ["ca_postcode"]
    assert ids("COUNTRY.ISO-3166-2") == ["countrycode_alpha2"]
    # IDENTITY.VAT_<COUNTRY> is mapped through its bound names
    assert ids("IDENTITY.VAT_IT") == ["it_iva"]
    assert ids("IDENTITY.VAT_DE") == []
    # locale-bound names resolve through FTA's placeholder ...
    assert ids("MONTH.FULL_fr-FR") == ["month"]
    assert ids("GENDER.TEXT_DE") == ["gender"]
    assert ids("STREET_ADDRESS_NL") == ["street_address"]
    # ... and an exact name wins over the placeholder
    assert ids("STREET_ADDRESS_JA") == ["address"]
    assert ids("CHECKDIGIT.LUHN") == []
    # every FTA type maps to at most one registry record
    seen: dict[str, str] = {}
    for record in reg.datatypes.values():
        value = record.get("mappings", {}).get("fta")
        for name in value if isinstance(value, list) else [value] if value else []:
            assert name not in seen, f"{name} is mapped by {seen[name]} and {record['id']}"
            seen[name] = record["id"]
    assert len(seen) >= 250


def test_fta_tool_lists_the_mapped_records(repo_sources):
    mapped = {
        rec.id for rec in repo_sources.datatypes if (rec.data.get("mappings") or {}).get("fta")
    }
    assert effective_supported_types(repo_sources)["fta"] == sorted(mapped)


def test_fta_mapping_must_be_an_fta_type(mini_data):
    path = mini_data / "datatypes/any/pii/email.yaml"
    path.write_text(path.read_text() + "mappings:\n  fta: email\n")
    errors = [str(i) for i in validate(load_sources(mini_data)).errors]
    assert any("mappings" in e and "fta" in e for e in errors), errors

    for good in ("EMAIL", "COUNTRY.ISO-3166-2", "MONTH.FULL_<LOCALE>"):
        path.write_text(path.read_text().rsplit("  fta:", 1)[0] + f"  fta: {good}\n")
        assert validate(load_sources(mini_data)).errors == [], good


def test_sherlock_crosswalk(repo_sources):
    from metacrafter_registry import Registry

    reg = Registry.from_sources(DATA)

    def ids(label: str) -> list[str]:
        return [r["id"] for r in reg.crosswalk("sherlock", label)]

    assert ids("city") == ["city"]
    assert ids("birth Date") == ["birthday"]
    # the paper writes "Birth date" and Sato writes "birthDate": case and
    # spaces are ignored
    assert ids("Birth date") == ["birthday"]
    assert ids("birthDate") == ["birthday"]
    assert ids("fileSize") == ["filesize"]
    # a record can carry several Sherlock types
    assert ids("company") == ids("organisation") == ["orgname"]
    assert ids("sex") == ids("gender") == ["gender"]
    # new records for Sherlock types the registry did not have
    assert ids("birth Place") == ["birthplace"]
    assert ids("religion") == ["religion"]
    # generic header words and roles are not mapped
    assert ids("code") == []
    assert ids("director") == []
    # every Sherlock type maps to at most one registry record
    seen: dict[str, str] = {}
    for record in reg.datatypes.values():
        value = record.get("mappings", {}).get("sherlock")
        for label in value if isinstance(value, list) else [value] if value else []:
            assert label not in seen, f"{label} is mapped by {seen[label]} and {record['id']}"
            seen[label] = record["id"]
    assert len(seen) >= 32


def test_sherlock_schema_lists_the_78_types():
    schema = json.loads((REPO / "schema/datatype.schema.json").read_text("utf-8"))
    labels = schema["$defs"]["sherlockType"]["enum"]
    assert len(labels) == len(set(labels)) == 78
    assert {"birth Date", "birth Place", "file Size", "team Name"} <= set(labels)


def test_sherlock_tool_lists_the_mapped_records(repo_sources):
    mapped = sorted(
        rec.id for rec in repo_sources.datatypes if (rec.data.get("mappings") or {}).get("sherlock")
    )
    tool = next(t for t in repo_sources.tools if t.id == "sherlock")
    assert sorted(tool.data["supported_types"]) == mapped


def test_sherlock_mapping_must_be_a_sherlock_type(mini_data):
    path = mini_data / "datatypes/any/pii/email.yaml"
    path.write_text(path.read_text() + "mappings:\n  sherlock: email\n")
    errors = [str(i) for i in validate(load_sources(mini_data)).errors]
    assert any("mappings" in e and "sherlock" in e for e in errors), errors

    path.write_text(path.read_text().replace("sherlock: email", "sherlock: name"))
    assert validate(load_sources(mini_data)).errors == []


# The labels of Sato's published model: "type78" in configs/types.json of
# megagonlabs/sato at commit c19ace3 (see devdocs/SATO_REVIEW.md).
SATO_TYPE78 = """
address affiliate affiliation age album area artist birthDate birthPlace brand capacity
category city class classification club code collection command company component
continent country county creator credit currency day depth description director duration
education elevation family fileSize format gender genre grades isbn industry jockey
language location manufacturer name nationality notes operator order organisation origin
owner person plays position product publisher range rank ranking region religion
requirement result sales service sex species state status symbol team teamName type
weight year
""".split()


def test_sato_types_are_the_sherlock_types():
    schema = json.loads((REPO / "schema/datatype.schema.json").read_text("utf-8"))
    sherlock = schema["$defs"]["sherlockType"]["enum"]

    def key(label: str) -> str:
        return "".join(label.split()).lower()

    assert len(SATO_TYPE78) == len(set(SATO_TYPE78)) == 78
    assert sorted(map(key, SATO_TYPE78)) == sorted(map(key, sherlock))


def test_sato_crosswalk(repo_sources):
    from metacrafter_registry import Registry

    reg = Registry.from_sources(DATA)

    def ids(system: str, label: str) -> list[str]:
        return [r["id"] for r in reg.crosswalk(system, label)]

    assert ids("sato", "birthDate") == ["birthday"]
    assert ids("sato", "birthPlace") == ["birthplace"]
    assert ids("sato", "fileSize") == ["filesize"]
    assert ids("sato", "company") == ["orgname"]
    # generic header words and team names are not mapped
    assert ids("sato", "code") == []
    assert ids("sato", "teamName") == []
    # every Sato label resolves exactly as the Sherlock label does
    for label in SATO_TYPE78:
        assert ids("sato", label) == ids("sherlock", label), label


def test_sato_tool_lists_the_sherlock_records(repo_sources):
    mapped = sorted(
        rec.id for rec in repo_sources.datatypes if (rec.data.get("mappings") or {}).get("sherlock")
    )
    tool = next(t for t in repo_sources.tools if t.id == "sato")
    assert tool.data["category"] == "detector"
    assert sorted(tool.data["supported_types"]) == mapped


def test_autotype_crosswalk(repo_sources):
    from metacrafter_registry import Registry

    reg = Registry.from_sources(DATA)

    def ids(case: str) -> list[str]:
        return [r["id"] for r in reg.crosswalk("autotype", case)]

    assert ids("isbn") == ["isbn10"]
    assert ids("date-chinese") == ["date"]
    assert ids("ssn - new") == ["usssn"]
    # new records for benchmark types the registry lacked
    assert ids("canpost") == ["ca_fsa"]
    assert ids("bibcode") == ["bibcode"]
    # a file name or a data_release path resolves too
    assert ids("isbn.txt") == ["isbn10"]
    assert ids("data_release/japan address.txt") == ["address"]
    # message formats and mislabelled test cases are not mapped
    assert ids("SWIFT") == []
    assert ids("ric") == []
    # every test case maps to at most one registry record
    seen: dict[str, str] = {}
    for record in reg.datatypes.values():
        value = record.get("mappings", {}).get("autotype")
        for case in value if isinstance(value, list) else [value] if value else []:
            assert case not in seen, f"{case} is mapped by {seen[case]} and {record['id']}"
            seen[case] = record["id"]
    assert len(seen) == 119


def test_autotype_mapping_must_be_a_test_case_name(mini_data):
    path = mini_data / "datatypes/any/pii/email.yaml"
    path.write_text(path.read_text() + "mappings:\n  autotype: email.txt\n")
    errors = [str(i) for i in validate(load_sources(mini_data)).errors]
    assert any("mappings" in e and "autotype" in e for e in errors), errors

    path.write_text(path.read_text().replace("autotype: email.txt", "autotype: email"))
    assert validate(load_sources(mini_data)).errors == []


def test_gs1_ai_crosswalk(repo_sources):
    from metacrafter_registry import Registry

    reg = Registry.from_sources(DATA)

    def ids(ai: str) -> list[str]:
        return [r["id"] for r in reg.crosswalk("gs1_ai", ai)]

    assert ids("00") == ["sssc"]
    assert ids("01") == ["gtin"]
    # as printed under a barcode, and as a GS1 vocabulary IRI
    assert ids("(414)") == ["gs1_ai_414"]
    assert ids("https://ref.gs1.org/ai/8003") == ["gs1_ai_8003"]
    assert reg.get("gs1_ai_8003")["semantic_type"] == "grai"
    assert reg.get("gs1_ai_410")["semantic_type"] == "gln"
    # AIs that carry a non-GS1 identifier map to its record
    assert ids("8007") == ["iban"]
    assert ids("8041") == ["imei"]
    # data attributes are not mapped
    assert ids("17") == []
    assert ids("3103") == []
    # every AI maps to at most one record
    seen: dict[str, str] = {}
    for record in reg.datatypes.values():
        value = record.get("mappings", {}).get("gs1_ai")
        for ai in value if isinstance(value, list) else [value] if value else []:
            assert ai not in seen, f"{ai} is mapped by {seen[ai]} and {record['id']}"
            seen[ai] = record["id"]
    assert len(seen) == 38


def test_gs1_element_string_records_are_consistent(repo_sources):
    """gs1_ai_<AI> maps to <AI>; its examples start with the AI and, for a
    pattern, the data field after the AI is a valid value of the key record."""
    import re

    from metacrafter_registry.checksums import ALGORITHMS

    records = {rec.id: rec.data for rec in repo_sources.datatypes}
    element = {rid: data for rid, data in records.items() if rid.startswith("gs1_ai_")}
    assert len(element) == 31
    for rid, data in element.items():
        ai = rid.removeprefix("gs1_ai_")
        assert data["mappings"]["gs1_ai"] == ai, rid
        assert data["regexp"].startswith(f"^{ai}"), rid
        key = records.get(data.get("semantic_type"))
        for example in data["examples"]:
            if example.get("valid") is False:
                continue
            assert example["value"].startswith(ai), (rid, example)
            if key is None:
                continue
            field = example["value"][len(ai) :]
            if ai == "8003":  # AI 8003 writes a filler zero before the GRAI
                field = field[1:]
            assert re.search(key["regexp"], field), (rid, field)
            if key.get("checksum"):
                assert ALGORITHMS[key["checksum"]](field), (rid, field)


def test_gs1_ai_mapping_must_be_an_ai_string(mini_data):
    path = mini_data / "datatypes/any/pii/email.yaml"
    original = path.read_text()
    for bad in ("1", "'(01)'", "'01a'", "'80030'"):
        path.write_text(original + f"mappings:\n  gs1_ai: {bad}\n")
        errors = [str(i) for i in validate(load_sources(mini_data)).errors]
        assert any("mappings" in e and "gs1_ai" in e for e in errors), (bad, errors)

    for good in ("'01'", "'8003'", "['8040', '8041']"):
        path.write_text(original + f"mappings:\n  gs1_ai: {good}\n")
        assert validate(load_sources(mini_data)).errors == [], good


def test_orgid_crosswalk(repo_sources):
    from metacrafter_registry import Registry

    reg = Registry.from_sources(DATA)

    def ids(value: str) -> list[str]:
        return [r["id"] for r in reg.crosswalk("orgid", value)]

    assert ids("GB-COH") == ["companyhouseid"]
    assert ids("XI-LEI") == ["lei"]
    # a whole ORG-ID.guide identifier, any case, or the list page URL
    assert ids("GB-COH-09506232") == ["companyhouseid"]
    assert ids("gb-coh") == ["companyhouseid"]
    assert ids("https://org-id.guide/list/RU-INN") == ["inn"]
    assert ids("XI-PB-gb/aberdeen-city-council") == ["okfn_public_body"]
    assert ids("CA_NS-NVS_NVE-1542067") == ["ca_ns_registry_id"]
    # deprecated codes resolve to the record of the list that replaced them
    assert ids("SE-BLV") == ["seorgnumber"]
    assert ids("IT-RI") == ["it_iva"]
    assert ids("XE-EXAMPLE") == []
    # every ORG-ID.guide code maps to at most one registry record
    seen: dict[str, str] = {}
    for record in reg.datatypes.values():
        value = record.get("mappings", {}).get("orgid")
        for code in value if isinstance(value, list) else [value] if value else []:
            assert code not in seen, f"{code} is mapped by {seen[code]} and {record['id']}"
            seen[code] = record["id"]
    assert len(seen) >= 250


def test_orgid_mapping_must_be_a_list_code(mini_data):
    path = mini_data / "datatypes/any/pii/email.yaml"
    path.write_text(path.read_text() + "mappings:\n  orgid: gb-coh\n")
    errors = [str(i) for i in validate(load_sources(mini_data)).errors]
    assert any("mappings" in e and "orgid" in e for e in errors), errors

    path.write_text(path.read_text().replace("orgid: gb-coh", "orgid: GB-COH-09506232"))
    assert validate(load_sources(mini_data)).errors

    for good in ("GB-COH", "CA_ON-ONT", "BE-BCE_KBO", "[XI-LEI, XI-GRID]"):
        path.write_text(path.read_text().rsplit("  orgid:", 1)[0] + f"  orgid: {good}\n")
        assert validate(load_sources(mini_data)).errors == [], good


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


def _javascript_identify(tmp_path, index_path, cases, limit):
    """[[id, score], ...] from identify-core.js for each (values, field_name) case."""
    script = tmp_path / "run.js"
    script.write_text(
        "const core = require(process.argv[2]);\n"
        "const index = require(process.argv[3]);\n"
        "const cases = JSON.parse(process.argv[4]);\n"
        "const limit = Number(process.argv[5]);\n"
        "console.log(JSON.stringify(cases.map(([v, f]) => "
        "core.identify(index, v, f, null, limit).map(r => [r.id, r.score]))));\n"
    )
    out = subprocess.run(
        [
            "node",
            str(script),
            str(REPO / "src/metacrafter_registry/static/identify-core.js"),
            str(index_path),
            json.dumps(cases),
            str(limit),
        ],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return json.loads(out)


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
        (["2025-05-15", "1990-01-31"], "birthday"),
    ]
    js = _javascript_identify(tmp_path, built_site / "identify-index.json", cases, 3)
    for (values, field), js_top in zip(cases, js, strict=True):
        py_top = [[r["id"], r["score"]] for r in reg.identify(values, field_name=field, limit=3)]
        assert js_top[0] == py_top[0], (values, js_top, py_top)


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")
def test_javascript_compact_matches_match_python(reg_with_date, tmp_path):
    """Both scorers ignore a compact-form match that a more specific regexp claims
    and weight the other compact-form matches the same way."""
    from conftest import ISO_DATES

    from metacrafter_registry.agents import identify_index

    index = tmp_path / "identify-index.json"
    index.write_text(
        json.dumps(identify_index(reg_with_date.datatypes.values(), reg_with_date._broadness))
    )
    cases = [
        (ISO_DATES, "birthday"),
        (ISO_DATES, "cardPeriod"),
        (["4111 1111 1111 1111"], ""),
        (["4111-1111-1111-1111", "5500 0000 0000 0004"], "card"),
        (["45 397 000"], ""),
        (["GB82 WEST 1234 5698 7654 32"], ""),
        # Compact-form hits without a check digit count half.
        (["01001-000", "01310-100"], ""),
        (["432 5251 79"], ""),
    ]
    js = _javascript_identify(tmp_path, index, cases, 5)
    for (values, field), js_top in zip(cases, js, strict=True):
        py_top = [
            [r["id"], r["score"]] for r in reg_with_date.identify(values, field_name=field, limit=5)
        ]
        assert js_top == py_top, (values, js_top, py_top)
    assert js[0][0][0] == js[1][0][0] == "date"


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
        "00095287650000315043",
        "1987654Ad4X4bL5ttr2310c2K",
        "1987654Ad4X4bL5ttr2310cXK",
        "12345_!\"%&'()*+,-./LC",
        "9528765Model-A7NM",
        "22",
        "!22",
        "2",
        "PL 856-734-62-15",
        "SK 202 274 96 19",
        "SI 5022 3054",
        "SE556012579001",
    ]
    values += [str(rng.randrange(10**16, 10**18)) for _ in range(300)]
    values += [str(rng.randrange(10**8, 10**15)) for _ in range(300)]
    values += [f"ATU{rng.randrange(10**8):08d}" for _ in range(100)]
    values += [f"BG{rng.randrange(10**10):010d}" for _ in range(100)]
    values += [
        f"{rng.randrange(10**5):05d}2{rng.choice('AB')}{rng.randrange(10**8):08d}"
        for _ in range(100)
    ]
    values += [f"{rng.randrange(10**11):011d}" for _ in range(1000)]
    values += [f"PL{rng.randrange(10**10):010d}" for _ in range(300)]
    values += [f"SK{rng.randrange(10**10):010d}" for _ in range(300)]
    values += [f"SI{rng.randrange(10**8):08d}" for _ in range(300)]
    values += [f"SE{rng.randrange(10**10):010d}0{rng.choice('12')}" for _ in range(300)]
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
