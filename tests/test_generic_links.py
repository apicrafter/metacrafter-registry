"""Generic links that tools use to accept a broader label (metacrafter-registry #159).

A classifier label is right for an expected type when it is that type or one reachable through
`parent` / `semantic_type`. National types without the link make right labels look wrong.
"""

from __future__ import annotations

import pytest


@pytest.fixture(scope="module")
def records(repo_sources):
    return {r.data["id"]: r.data for r in repo_sources.datatypes}


def generic(records, dt):
    seen, todo = set(), [dt]
    while todo:
        cur = todo.pop()
        if cur in seen or cur not in records:
            continue
        seen.add(cur)
        todo += [records[cur][k] for k in ("parent", "semantic_type") if records[cur].get(k)]
    return seen


def test_national_postcodes_are_postindex(records):
    postcodes = [
        i
        for i in records
        if i != "postindex" and any(w in i for w in ("postcode", "zipcode", "postalcode"))
    ]
    assert len(postcodes) > 40
    assert [i for i in postcodes if "postindex" not in generic(records, i)] == []


@pytest.mark.parametrize(
    "dt,broader",
    [
        ("gbpostcode", "postindex"),
        ("plpostcode", "postindex"),
        ("fr_commune", "city"),
        ("it_comune", "city"),
        ("atcity", "city"),
        ("de_kreisschluessel", "de_ars"),
        ("iso3166code_compact", "iso3166code"),
    ],
)
def test_generic_link(records, dt, broader):
    assert broader in generic(records, dt)


@pytest.mark.parametrize(
    "dt,broader",
    [
        # #154 transport
        ("gtfs_location_type", "category"),
        ("gtfs_wheelchair_boarding", "category"),
        ("gb_naptan_atco", "id"),
        ("ifopt_stop_id", "id"),
        ("es_adif_station_code", "id"),
        ("kr_bus_stop_ars", "id"),
        # #155 dates and calendars
        ("date_jp_era", "date"),
        ("year_jp_era", "year"),
        ("date_roc", "date"),
        ("yearmonth_roc", "yearmonth"),
        ("date_dmony", "date"),
        ("jp_estat_time_code", "jp_estat_time_code"),
        # #156 administrative and statistical codes
        ("co_divipola", "co_municipality"),
        ("br_siafi_municipality_code", "br_municipality"),
        ("mx_inegi_municipality_code", "mx_municipality"),
        ("us_census_sumlev", "category"),
        ("us_census_region", "category"),
        ("us_census_division", "category"),
        ("us_census_lsad", "category"),
        ("us_nyc_bbl", "usparcelnumber"),
        ("us_nyc_bin", "id"),
        ("ua_budget_code", "ua_budget_code"),
        # #157 register identifiers
        ("fr_museofile", "id"),
        ("fr_merimee", "id"),
        ("fr_irve_id", "id"),
        ("nl_brin_vestiging", "nl_brin"),
        ("us_cms_ccn", "id"),
        # #158
        ("eea_eoi_station_code", "id"),
        ("dwc_basis_of_record", "category"),
        ("sharepoint_content_type_id", "id"),
        ("area", "numeric"),
    ],
)
def test_testdata_types(records, dt, broader):
    """Datatypes proposed from metacrafter-testdata (#154-#158) exist with their generic link."""
    assert dt in records
    assert broader in generic(records, dt)


@pytest.mark.parametrize("dt", ["fr_pdl", "pl_ade"])
def test_personal_identifiers_are_pii(records, dt):
    assert records[dt]["is_pii"] is True
