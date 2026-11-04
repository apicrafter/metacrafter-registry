from __future__ import annotations

import json

import pytest

from metacrafter_registry import Registry
from metacrafter_registry.checksums import (
    at_uid,
    bg_vat,
    es_dni,
    fi_hetu,
    fr_nir,
    gtin,
    iban_mod97,
    isbn10,
    isbn13,
    it_codicefiscale,
    it_iva,
    luhn,
    no_fnr,
    ru_inn,
    ru_ogrn,
    ru_snils,
)
from metacrafter_registry.serve import running_server


@pytest.fixture(scope="module")
def reg(repo_sources):
    from conftest import DATA

    return Registry.from_sources(DATA)


def test_checksum_reference_values():
    assert luhn("4111 1111 1111 1111") and not luhn("4111111111111112")
    assert luhn("490154203237518")  # IMEI
    assert iban_mod97("GB82 WEST 1234 5698 7654 32") and not iban_mod97("GB82WEST12345698765433")
    assert gtin("036000291452") and gtin("4006381333931") and not gtin("4006381333932")
    assert isbn13("978-0-521-29366-2") and isbn10("0-521-22151-X") and not isbn10("0521221519")
    assert ru_inn("7707083893") and ru_inn("500100732259") and not ru_inn("7707083894")
    assert ru_snils("112-233-445 95") and not ru_snils("112-233-445 96")
    assert ru_ogrn("1027700132195") and not ru_ogrn("1027700132196")
    # Reference values from the python-stdnum documentation.
    assert fr_nir("2 95 10 99 126 111 93") and not fr_nir("295109912611199")
    assert fr_nir("253072B07300470") and fr_nir("253072A07300443")
    assert not fr_nir("253072C07300443")
    assert at_uid("ATU13585627") and at_uid("U13585627") and not at_uid("ATU13585626")
    assert bg_vat("BG175074752") and bg_vat("175074752") and not bg_vat("BG175074751")
    assert no_fnr("151086 95088") and not no_fnr("15108695077")
    assert it_codicefiscale("RCCMNL83S18D969H") and it_codicefiscale("CNTCHR83T41D969D")
    assert not it_codicefiscale("RCCMNL83S18D969A") and not it_codicefiscale("RCCMNL83Z18D969H")
    assert it_iva("IT 00743110157") and it_iva("00743110157") and not it_iva("00743110158")
    assert not it_iva("00743115007")  # 500 is not a tax office code
    assert fi_hetu("131052-308T") and not fi_hetu("131052-308U") and not fi_hetu("131052308T")
    assert es_dni("54362315-K") and not es_dni("54362315Z")


def test_lookup_and_aliases(reg):
    assert reg.get("ssn")["id"] == "usssn"
    assert "guid" in reg and "nothing_like_this" not in reg
    assert reg.url_for("ssn") == "https://registry.apicrafter.io/datatype/usssn"


def test_identify_inn_by_values_and_field_name(reg):
    top = reg.identify(["7707083893", "7728168971"], field_name="inn")[0]
    assert top["id"] == "inn" and top["score"] == 100
    assert top["checksum"] == {"algorithm": "ru_inn", "pass_rate": 1.0}


def test_identify_iban_without_field_name(reg):
    values = [
        "GB82 WEST 1234 5698 7654 32",
        "DE89370400440532013000",
        "FR1420041010050500013M02606",
    ]
    top = reg.identify(values)[0]
    assert top["id"] == "iban"
    assert top["checksum"]["pass_rate"] == 1.0


def test_identify_card_numbers_written_with_spaces(reg):
    assert reg.identify(["4111 1111 1111 1111"], field_name="card")[0]["id"] == "bankcard"


def test_catch_all_regexps_rank_low(reg):
    candidates = {c["id"]: c for c in reg.identify(["user@example.com"], limit=50)}
    assert candidates["email"]["score"] > candidates.get("fqdn", {"score": 0})["score"]


def test_search_and_filters(reg):
    hits = reg.search("passport", country="GB")
    assert [h["id"] for h in hits] == ["ukpassport"]
    assert all(h["status"] == "stable" for h in reg.search("", status="stable", limit=50))


def test_crosswalk_and_match(reg):
    wikidata_url = "https://www.wikidata.org/wiki/Property:P1243"
    assert [r["id"] for r in reg.crosswalk("wikidata", wikidata_url)] == ["isrc"]
    matches = [r["id"] for r in reg.match("0x5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAed")]
    assert "ethereum_address" in matches
    assert "bankcard" in [r["id"] for r in reg.match("4111111111111111")]
    assert "bankcard" not in [r["id"] for r in reg.match("4111111111111112")]  # Luhn fails


def test_load_snapshot_and_fetch_with_cache(built_site, tmp_path):
    snapshot = Registry.load(built_site / "api" / "v1")
    assert snapshot.get("email")["id"] == "email" and snapshot.version
    with running_server(built_site) as base:
        fetched = Registry.fetch(base, cache_dir=tmp_path)
        assert len(fetched) == len(snapshot)
        again = Registry.fetch(base, cache_dir=tmp_path)
        assert again.source.endswith("(cached)")


def test_fetch_rejects_tampered_files(built_site, tmp_path):
    import shutil

    site = tmp_path / "site"
    shutil.copytree(built_site, site)
    path = site / "api" / "v1" / "aliases.json"
    path.write_text(json.dumps({"tampered": "email"}), "utf-8")
    with running_server(site) as base:
        with pytest.raises(ValueError, match="SHA-256"):
            Registry.fetch(base, cache_dir=tmp_path / "cache")
