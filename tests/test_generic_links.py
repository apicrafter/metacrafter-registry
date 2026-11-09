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


@pytest.mark.parametrize(
    "dt,broader",
    [
        ("opening_hours", "timerange"),
        ("unixtime", "datetime"),
        # A height label is right for an elevation (SMHI station height), and a province label
        # for the first-level provinces of a country (metacrafter-rules #60).
        ("elevation", "height"),
        ("thprovince", "province"),
        ("caprovince", "province"),
        ("caprovincecode", "province"),
        ("nl_province", "province"),
        ("idprovince", "province"),
        ("vnprovince", "province"),
        ("krprovince", "province"),
        ("za_province", "province"),
        ("ec_province", "province"),
        ("thprovince", "admin_area_1"),
    ],
)
def test_links_162(records, dt, broader):
    """Links found while scoring metacrafter-testdata (#162)."""
    assert broader in generic(records, dt)


def test_okvalpha_is_an_alias_of_iso4217curcode(records):
    """The alphabetic OKV codes are the ISO 4217 codes (#162): okvalpha is an alias, so a
    label okvalpha is right where ISO 4217 codes are expected."""
    assert "okvalpha" not in records
    assert "okvalpha" in records["iso4217curcode"]["aliases"]


def test_eunuts_is_an_alias_of_nutsregion(records):
    """eunuts and nutsregion were two records for the NUTS code (#162): eunuts is now an alias."""
    assert "eunuts" not in records
    assert "eunuts" in records["nutsregion"]["aliases"]


@pytest.mark.parametrize(
    "dt,broader",
    [
        # #161 open register and science files
        ("us_ntee_code", "category"),
        ("gleif_ra_code", "id"),
        ("ru_cbr_regnum", "id"),
        ("content_license", "category"),
        ("gadm_gid", "id"),
        ("dwc_taxonomic_status", "category"),
        ("dwc_taxon_rank", "category"),
        # #163 identifiers
        ("gr_gemi", "id"),
        ("nz_company_number", "id"),
        ("eu_pic", "id"),
        ("eu_grant_agreement_number", "id"),
        ("tr_ikn", "id"),
        ("ro_lmi_code", "id"),
        ("lt_kvr_code", "id"),
        ("cz_library_registration_number", "id"),
        # #164 bank codes
        ("hu_giro_code", "id"),
        ("ua_mfo", "id"),
        ("in_micr", "id"),
        # #165 school and health facility codes
        ("gr_school_code", "id"),
        ("ro_siiir_code", "id"),
        ("ro_sirues_code", "id"),
        ("rs_jisp_id", "id"),
        ("fi_oppilaitosnumero", "id"),
        ("za_emis_number", "id"),
        ("id_npsn", "id"),
        ("ke_mfl_code", "id"),
        ("hu_neak_code", "id"),
        ("vn_kcb_code", "id"),
        ("id_puskesmas_code", "id"),
        # #166 administrative and address codes
        ("bg_nsi_oblast_code", "category"),
        ("bg_nsi_obshtina_code", "category"),
        ("bg_nsi_kmetstvo_code", "id"),
        ("hu_jaras_code", "id"),
        ("ee_ehak", "category"),
        ("se_lanskod", "category"),
        ("lt_municipality_code", "category"),
        ("eu_lau_code", "id"),
        ("hdx_pcode", "id"),
        ("admin_area_3", "location"),
        ("cz_ruian_address_point", "id"),
        ("lv_var_address_code", "id"),
        ("ee_ads_adr_id", "id"),
        # #167 classifications
        ("kz_kpved", "category"),
        ("lt_evrk", "eu_nace"),
        ("se_ssyk", "isco08"),
        ("ev_connector_type", "category"),
        # #168
        ("era_rinf_op_id", "id"),
        ("excel_serial_date", "date"),
        ("year_th_be", "year"),
        ("ar_month", "month"),
        ("libris_id", "url"),
    ],
)
def test_testdata_types_161_168(records, dt, broader):
    """Datatypes proposed from metacrafter-testdata (#161, #163-#168) exist with their generic link."""
    assert dt in records
    assert records[dt]["status"] == "draft"
    assert broader in generic(records, dt)
