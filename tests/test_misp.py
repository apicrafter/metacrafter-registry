"""mappings.misp: MISP attribute types."""

from __future__ import annotations

import pytest
from conftest import DATA

from metacrafter_registry import Registry
from metacrafter_registry.client import _misp_type
from metacrafter_registry.loader import load_sources
from metacrafter_registry.validate import validate

# MISP types that say where a value was seen (source, destination, target,
# WHOIS record) rather than what it is. Registry records are not directional.
DIRECTIONAL = {
    "ip-src",
    "ip-dst",
    "ip-src|port",
    "ip-dst|port",
    "email-src",
    "email-dst",
    "email-reply-to",
    "target-email",
    "target-user",
    "target-machine",
    "whois-registrant-email",
    "whois-registrant-phone",
    "dns-soa-email",
}


@pytest.fixture(scope="module")
def registry():
    return Registry.from_sources(DATA)


def test_misp_mapping_checks_its_format(mini_data):
    path = mini_data / "datatypes/any/pii/email.yaml"
    original = path.read_text()
    bad = (
        "mac_address",
        "IP-SRC",
        "Email",
        "as",
        "'misp:type=\"email\"'",
        "https://www.misp-project.org/datamodels/",
        "'ip-src|'",
    )
    good = ("email", "AS", "sha512/256", "'filename|md5'", "named pipe", "[domain, hostname]")
    for value in bad:
        path.write_text(original + f"mappings:\n  misp: {value}\n")
        errors = [str(i) for i in validate(load_sources(mini_data)).errors]
        assert any("mappings" in e and "misp" in e for e in errors), (value, errors)
    for value in good:
        path.write_text(original + f"mappings:\n  misp: {value}\n")
        assert validate(load_sources(mini_data)).errors == [], value


def test_misp_crosswalk_normalization():
    assert _misp_type("vulnerability") == "vulnerability"
    assert _misp_type(" MAC-Address ") == "mac-address"
    assert _misp_type('misp:type="ip-src"') == "ip-src"
    assert _misp_type("misp:type=vulnerability") == "vulnerability"
    assert _misp_type("as") == "AS"
    assert _misp_type("AS") == "AS"
    assert _misp_type("sha512/256") == "sha512/256"


def test_misp_crosswalk(registry):
    def ids(value: str) -> list[str]:
        return sorted(r["id"] for r in registry.crosswalk("misp", value))

    # the correspondences listed in devdocs/SOURCES_GAP_2026-11.md
    assert "cve_id" in ids("vulnerability")
    assert ids("weakness") == ["cwe_id"]
    assert ids("cpe") == ["cpe23"]
    assert ids("ja3-fingerprint-md5") == ["ja3_fingerprint"]

    assert ids('misp:type="vulnerability"') == ids("vulnerability")
    assert ids("MAC-ADDRESS") == ["mac_address"]
    assert ids("as") == ["asn"]
    assert ids("hostname") == ["fqdn"]
    assert ids("btc") == ["p2pkhaddr", "p2shaddr", "p2traddr", "p2wpkhaddr", "p2wshaddr"]
    assert ids("ip-src") == []


def test_no_record_maps_a_directional_misp_type(repo_sources):
    for rec in repo_sources.datatypes:
        value = (rec.data.get("mappings") or {}).get("misp")
        values = value if isinstance(value, list) else [value] if value else []
        assert not DIRECTIONAL & set(values), (rec.id, values)


def test_record_page_shows_misp_types(built_site):
    page = (built_site / "datatype/fqdn.html").read_text("utf-8")
    assert "<dt>MISP attribute type</dt>" in page
    assert "<code>domain</code>, <code>hostname</code>" in page
    assert '"misp": "vulnerability"' in (built_site / "datatype/cve_id.json").read_text("utf-8")
