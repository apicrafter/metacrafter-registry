from __future__ import annotations

import json

import pytest

from metacrafter_registry import Registry
from metacrafter_registry.checksums import (
    at_uid,
    base58check,
    bech32,
    bech32m,
    bg_vat,
    de_fsnr,
    de_idnr,
    de_ik,
    de_kvnr,
    de_lanr,
    de_pzn,
    de_rvnr,
    de_ustidnr,
    de_widnr,
    es_dni,
    fi_hetu,
    fr_nir,
    gs1_checkpair,
    gs1_mod10,
    gtin,
    iban_mod97,
    isbn10,
    isbn13,
    iso7064_mod97_10,
    it_codicefiscale,
    it_iva,
    kz_iin_bin,
    luhn,
    no_fnr,
    pl_nip,
    ru_inn,
    ru_ogrn,
    ru_snils,
    se_vat,
    si_ddv,
    sk_dph,
)
from metacrafter_registry.serve import running_server


@pytest.fixture(scope="module")
def reg(repo_sources):
    from conftest import DATA

    return Registry.from_sources(DATA)


def test_gs1_checksums():
    # GS1 check digit of any length: GTIN-14, GLN, SSCC, and the SSCC element string
    assert gs1_mod10("09506000134352") and not gs1_mod10("09506000134353")
    assert gs1_mod10("0865321000104")
    assert gs1_mod10("095287650000315043") and gs1_mod10("00095287650000315043")
    assert not gs1_mod10("7") and not gs1_mod10("95A")
    # GS1 check character pair: test values of lint_csumalpha.c (GS1 Barcode Syntax Engine)
    for good in (
        "22",
        "!22",
        "1987654Ad4X4bL5ttr2310c2K",
        "12345678901234567890123NT",
        "12345_ABCDEFGHIJKLMCP",
        "12345_abcdefghijklmN3",
        "12345_!\"%&'()*+,-./LC",
        "12345_0123456789:;<=>?62",
        "7907665Bm8v2AB",
        "97850l6KZm0yCD",
    ):
        assert gs1_checkpair(good), good
    for bad in ("", "2", "33", "1987654Ad4X4bL5ttr2310cXK", "1987654Ad4X4bL5ttr2310c2X"):
        assert not gs1_checkpair(bad), bad


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
    assert pl_nip("PL 8567346215") and pl_nip("856-734-62-15") and not pl_nip("PL 8567346216")
    assert sk_dph("SK 202 274 96 19") and not sk_dph("SK 202 274 96 18")
    assert si_ddv("SI 5022 3054") and si_ddv("50223054") and not si_ddv("SI 50223055")
    assert se_vat("SE556012579001") and se_vat("556012-5790 01")
    assert not se_vat("SE556012579101") and not se_vat("SE556012579002")
    assert kz_iin_bin("950440001673") and kz_iin_bin("500101100010")
    assert kz_iin_bin("500101100106")  # the first weights give 10
    assert not kz_iin_bin("950440001674") and not kz_iin_bin("95044000167")
    assert de_ustidnr("DE136695976") and de_ustidnr("136695976") and not de_ustidnr("136695978")
    assert de_widnr("DE136695976-00001") and not de_widnr("DE136695978-00001")
    assert not de_widnr("DE136695976")
    assert de_idnr("36 574 261 809") and not de_idnr("36574261890")
    assert not de_idnr("36554266806")  # two digits repeated
    assert de_idnr("36574261868") and de_idnr("36657426182")  # a digit three times
    assert not de_idnr("36665742182")  # three equal digits side by side
    assert de_rvnr("15 070649 C 103") and not de_rvnr("15 070649 C 104")
    assert de_kvnr("A123456780") and not de_kvnr("A123456781")
    assert de_ik("260326822") and not de_ik("260326823")
    assert de_lanr("381925801") and not de_lanr("381925301")
    assert de_pzn("27580899") and de_pzn("PZN-27580899") and de_pzn("2758089")
    assert not de_pzn("27580898")
    assert de_fsnr("B072RRE2I55") and de_fsnr("B072RRE21X1") and not de_fsnr("B072RRE2I45")
    assert iso7064_mod97_10("991-03730-19") and not iso7064_mod97_10("991-03730-18")


def test_crypto_checksum_reference_values():
    # Bitcoin Wiki sample address and WIF key; BIP-32 test vector 1 (chain m)
    assert base58check("1PMycacnJaSqwwJqjawXBErnLsZ7RkXUAs")
    assert base58check("3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLy")
    assert base58check("5HueCGU8rMjxEXxiPuD5BDku4MkFqeZyd4dZ1jvhTVqvbTLvyTJ")
    assert base58check(
        "xpub661MyMwAqRbcFtXgS5sYJABqqG9YLmC4Q1Rdap9gSE8NqtwybGhePY2gZ29ESFjqJoCu1Rupje8YtGqsefD265TMg7usUDFdp6W1EGMcet8"
    )
    assert base58check("1111111111111111111114oLvT2")  # leading zero bytes
    assert not base58check("1PMycacnJaSqwwJqjawXBErnLsZ7RkXUAt")
    assert not base58check("175tWpb8K1S7NmH4Zx6rewF9WQrcZv245W")  # BIP 21 example, bad checksum
    assert not base58check("0PMycacnJaSqwwJqjawXBErnLsZ7RkXUAs") and not base58check("")
    assert not base58check("1111")
    # BIP-173 and BIP-350 test vectors
    assert bech32("bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4")
    assert bech32("BC1QW508D6QEJXTDG4Y5R3ZARVARY0C5XW7KV8F3T4")
    assert bech32("bc1qrp33g0q5c5txsp9arysrx4k6zdkfs4nce4xj0gdcccefvpysxf3qccfmv3")
    assert not bech32("bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t5")
    assert not bech32("bc1qW508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4")  # mixed case
    assert not bech32("bc1p0xlxvlhemja6c4dqv22uapctqupfhlxm9h8z3k2e72q4k9hcz7vqzk5jj0")
    assert bech32m("bc1p0xlxvlhemja6c4dqv22uapctqupfhlxm9h8z3k2e72q4k9hcz7vqzk5jj0")
    assert not bech32m("bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4")
    assert (
        not bech32("1qqqqqq")
        and not bech32("bc1qqqqq")
        and not bech32("bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3tb")
    )
    # no 90-character limit: a BOLT 11 example invoice
    assert bech32(
        "lnbc2500u1pvjluezsp5zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zygspp5qqqsyqcyq5rqwzqfqqqsyqcyq5rqwzqfqqqsyqcyq5rqwzqfqypqdq5xysxxatsyp3k7enxv4jsxqzpu9qrsgquk0rl77nj30yxdy8j9vdx85fkpmdla2087ne0xh8nhedh8w27kyke0lp53ut353s06fv3qfegext0eh0ymjpf39tuven09sam30g4vgpfna3rh"
    )


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


@pytest.mark.parametrize(
    ("values", "field", "expected"),
    [
        (["4111 1111 1111 1111"], "", "bankcard"),
        (["4111-1111-1111-1111", "5500 0000 0000 0004"], "card", "bankcard"),
        (["45 397 000", "45 397 000 001"], "oktmo", "oktmo"),
        (["GB82 WEST 1234 5698 7654 32"], "", "iban"),
    ],
)
def test_identify_values_written_with_separators(reg_with_date, values, field, expected):
    top = reg_with_date.identify(values, field_name=field)[0]
    assert top["id"] == expected and top["regexp_hit_rate"] == 1.0


@pytest.mark.parametrize("field", ["birthday", "cardPeriod", ""])
def test_identify_iso_dates_are_not_compact_digit_codes(reg_with_date, field):
    from conftest import ISO_DATES

    # Without hyphens an ISO date is eight digits: match() still accepts that.
    assert "okpo" in [r["id"] for r in reg_with_date.match(ISO_DATES[0])]
    candidates = {
        c["id"]: c for c in reg_with_date.identify(ISO_DATES, field_name=field, limit=100)
    }
    assert next(iter(candidates)) == "date"
    for rid in ("okpo", "oktmo"):
        assert not candidates.get(rid, {}).get("regexp_hit_rate")
        assert candidates.get(rid, {"score": 0})["score"] < candidates["date"]["score"]


def _record(rid, regexp, example, **fields):
    """A normalized stable datatype record; ``regexp`` None leaves it out."""
    record = {
        "id": rid,
        "name": rid,
        "kind": "datatype",
        "status": "stable",
        "is_pii": False,
        "examples": [{"value": example}],
        **fields,
    }
    if regexp is not None:
        record["regexp"] = regexp
    return record


def test_compact_match_yields_to_an_at_least_as_specific_raw_match():
    reg = Registry(
        [
            _record("iso_date", r"^\d{4}-\d{2}-\d{2}$", "2025-05-15"),
            _record("eight_digits", r"^\d{8}$", "12345678"),
            _record("sixteen_digits", r"^\d{16}$", "4111111111111111"),
            _record("digits_and_spaces", r"^[\d ]+$", "1 2"),
        ]
    )
    assert reg._broadness == {
        "iso_date": 0.0,
        "eight_digits": 0.0,
        "sixteen_digits": 0.0,
        "digits_and_spaces": 0.667,
    }
    hits = {
        c["id"]: c["regexp_hit_rate"] for c in reg.identify(["2025-05-15", "4111 1111 1111 1111"])
    }
    # "20250515" is not counted for eight_digits or digits_and_spaces: iso_date
    # matches "2025-05-15" as written and is at least as specific. The broader
    # digits_and_spaces does not stop sixteen_digits.
    assert hits == {"iso_date": 0.5, "sixteen_digits": 0.5, "digits_and_spaces": 0.5}


def test_a_match_as_written_outweighs_a_compact_form_match():
    reg = Registry(
        [
            _record("dash_date", r"^\d{4}-\d{2}-\d{2}$", "2024-12-25", status="draft"),
            _record("eight_digits", r"^\d{8}$", "12345678"),
            _record("issue_date", None, "2023-01-31"),
            _record("card16", r"^\d{16}$", "4111111111111111", checksum="luhn"),
        ]
    )
    # dash_date also matches the example of issue_date, so it is broader than
    # eight_digits and does not claim "20241225": both regexps count the dates.
    assert reg._broadness["dash_date"] > reg._broadness["eight_digits"]
    candidates = {c["id"]: c for c in reg.identify(["2024-12-25", "2023-01-31"])}
    assert list(candidates) == ["dash_date", "eight_digits"]
    assert candidates["eight_digits"]["regexp_hit_rate"] == 1.0
    # Matched only without hyphens, the dates count half: 60 x 0.5.
    assert candidates["eight_digits"]["score"] == 30
    assert candidates["dash_date"]["score"] == 35  # 60 x 1 x (1 - 1/3) - 5 for a draft

    # A compact-form match whose check digit passes counts in full.
    valid, invalid = reg.identify(["4111 1111 1111 1111"]), reg.identify(["4111 1111 1111 1112"])
    assert [(c["id"], c["score"]) for c in valid] == [("card16", 85)]  # 60 + 25 for luhn
    assert [(c["id"], c["score"]) for c in invalid] == [("card16", 30)]


def test_identify_iso_dates_rank_date_records_above_digit_codes(reg):
    # A draft date pattern with a broad regexp (date_ymd_dash, built here; the
    # registry maps YYYY-MM-DD to date itself). Stable eight-digit codes (okpo,
    # am_tin, ...) match ISO dates only without their hyphens and must not
    # outrank it. The stable date record, whose regexp also accepts ISO dates,
    # may rank above it.
    records = dict(reg.datatypes)
    records.setdefault(
        "date_ymd_dash",
        _record(
            "date_ymd_dash",
            r"^\d{4}-(?:0?[1-9]|1[0-2])-(?:0?[1-9]|[12]\d|3[01])$",
            "2024-12-25",
            status="draft",
            kind="pattern",
            semantic_type="date",
        ),
    )
    with_dates = Registry(records.values(), aliases=reg.aliases, manifest=reg.manifest)
    assert "okpo" in [r["id"] for r in with_dates.match("20241225")]
    candidates = {c["id"]: c for c in with_dates.identify(["2024-12-25", "2023-01-31"], limit=100)}
    assert next(iter(candidates)) in {"date", "date_ymd_dash"}
    dash = candidates["date_ymd_dash"]
    assert dash["regexp_hit_rate"] == 1.0
    for rid in ("okpo", "am_tin", "companyhouseid"):
        assert candidates.get(rid, {"score": 0})["score"] < dash["score"]


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
