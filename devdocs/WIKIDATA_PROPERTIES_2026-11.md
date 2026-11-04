# Wikidata external-identifier properties: review (2026-11-04)

Issue: [apicrafter/metacrafter-registry#19](https://github.com/apicrafter/metacrafter-registry/issues/19).

The issue asks to take more identifiers, and more data about identifiers
(examples, formats), from the
[Wikidata list of properties](https://www.wikidata.org/wiki/Wikidata:List_of_properties).

Related issues, not closed by this change:
[#21](https://github.com/apicrafter/metacrafter-registry/issues/21) (a sync
tool that refreshes names, descriptions, examples and regexps from Wikidata) and
[#48](https://github.com/apicrafter/metacrafter-registry/issues/48) (links to
Wikidata items, not only properties).

Sources, all read on 2026-11-04:

- The Wikidata Query Service: every property of type "external identifier",
  with its English label and description, format regexp (P1793, and the
  regexp of the format constraint), example values (P1855 with the property as
  qualifier), formatter URL (P1630), classes (P31), country (P17) and subject
  item (P1629).
- Up to 3,000 values of each property that this change uses, to test regexps.
- The usage counts of
  [Database reports/List of properties/all](https://www.wikidata.org/wiki/Wikidata:Database_reports/List_of_properties/all).
  The report lags: it shows 0 uses for some busy properties (ISIN, PubChem
  CID). For those properties the counts below come from a SPARQL `COUNT`.

## Summary

- Wikidata has **10,689 external-identifier properties**. 9,916 have a format
  regexp, 10,326 have example values and 10,099 have a formatter URL. 4,209 are
  used at least 1,000 times.
- Most of them identify a page or record in one web site or database, and
  many identify people (1,713 are classed as "authority control for people"). The
  registry needs the smaller set of identifiers that appear as values in
  datasets: codes of standards and classifications, register numbers of
  companies and places, identifiers of scholarly works, chemicals, genes,
  diseases and taxa, and some online account names.
- Before this change 144 records mapped to a Wikidata property. 43 of those
  properties are not external identifiers but strings, items or quantities,
  such as P281 postal code or P2044 elevation. Such a mapping is right when the
  record holds the values of that property; 41 of them are kept, see
  [Mappings to other property types](#mappings-to-other-property-types).
  **6 mappings were wrong.**
- **Done in this change:**
  - Fixed 6 wrong mappings: 5 removed, 1 corrected.
  - Mapped 35 existing records to the property that has the same meaning,
    and 10 records that the ORG-ID.guide review
    ([#17](https://github.com/apicrafter/metacrafter-registry/issues/17))
    added at the same time.
  - Corrected the regexp of 8 records (5 of them rejected almost every
    Wikidata value) and added a regexp to 16 records that had none.
  - Added examples from Wikidata to 25 existing records.
  - Added **92 new draft records**, one per Wikidata property, with a regexp
    tested against Wikidata values (91 of them) and examples from Wikidata.
  - Added `scripts/wikidata_properties.py`, which repeats the comparison.
- After this change 290 records map to 282 Wikidata properties (158 on `main`
  at the time of the merge). The share of records with a regexp went from
  57.3% to 62.0%, and with examples from 61.4% to 65.8%.

## Method

1. **Selection.** A property became a record when its values are a format that
   appears in datasets (a code, a register number, an accession number), it is
   issued by a standard body, a public register or a widely used database, and
   it is used on Wikidata. Properties that identify a page of one web site
   (encyclopedias, fan sites, sports statistics) and person-only authority files
   are left out.
2. **Regexp.** The Wikidata format regexp (P1793) was converted to Python:
   anchored with `^...$`, empty alternatives removed. It was tested with
   `re.fullmatch` against up to 3,000 Wikidata values. Where it failed on
   valid values, was too broad (`\d+`), used PCRE-only syntax (`\p{L}`) or
   left dots unescaped, it was rewritten and tested again. The "Matches"
   column below gives the result; the values that do not match are mostly
   errors in Wikidata (a URL, a name, a value with a suffix such as
   `2408.08921 [cs]`).
3. **Examples.** Example values are the property examples (P1855) of
   Wikidata, with the label of the Wikidata item as the description. Examples
   whose item is a human (P31 = Q5) were dropped, so the records contain no
   personal data. Three examples were checked separately in Wikidata and used
   instead of a doubtful one (NCBI taxon `9986`, labelled "Poponejo";
   EC number `1.1.1.1`, which validation flags as a placeholder; a YouTube
   channel of two singers).
4. **Descriptions** are written for the registry, from the Wikidata
   description and the documentation of the issuer. All new records are
   `status: draft`.
5. **Links** are the Wikidata property and, where they exist, the Wikipedia
   article and the documentation of the issuer. Every link was opened; a few
   sites answer HTTP 403 to scripts.

## Wrong mappings

| Record | Was | Now | Why |
|---|---|---|---|
| `cusip` | P5198 (ASC Leiden Thesaurus ID) | none | Wikidata has no CUSIP property |
| `isrc` | P435 (MusicBrainz work ID) | P1243 (ISRC) | wrong property |
| `mac_address` | P2817 (appears in the heritage monument list) | none | Wikidata has no MAC address property |
| `what3words` | P1566 (GeoNames ID) | none | Wikidata has no what3words property |
| `decountryname` | P297 (ISO 3166-1 alpha-2 code) | none | the record holds German country names, not codes |
| `wbregion` | P30 (continent) | none | World Bank regions are not continents |

The tests that used `mac_address` -> P2817 as their crosswalk example now use
`isrc` -> P1243.

## Mappings added to existing records

The mapping is added only when the record and the property mean the same
value. Two records that describe one identifier in two ways (for example
`abn` and `auabn`) both map to the property, as `eunuts` and `nutsregion`
already did.

| Record | Property | Wikidata label | Also changed |
|---|---|---|---|
| `isil` | [P791](https://www.wikidata.org/wiki/Property:P791) | ISIL |  |
| `isan` | [P3212](https://www.wikidata.org/wiki/Property:P3212) | ISAN |  |
| `ismn` | [P1208](https://www.wikidata.org/wiki/Property:P1208) | ISMN |  |
| `iso3166code` | [P300](https://www.wikidata.org/wiki/Property:P300) | ISO 3166-2 code | regexp, examples |
| `eu_nace` | [P4496](https://www.wikidata.org/wiki/Property:P4496) | NACE code rev.2 |  |
| `siret` | [P3215](https://www.wikidata.org/wiki/Property:P3215) | SIRET number |  |
| `siretcode` | [P3215](https://www.wikidata.org/wiki/Property:P3215) | SIRET number | regexp, examples |
| `jp_cn` | [P3225](https://www.wikidata.org/wiki/Property:P3225) | Corporate Number (Japan) |  |
| `usein` | [P1297](https://www.wikidata.org/wiki/Property:P1297) | IRS Employer Identification Number | regexp, examples |
| `no_orgnr` | [P2333](https://www.wikidata.org/wiki/Property:P2333) | Norwegian organisation number |  |
| `dk_cvr` | [P1059](https://www.wikidata.org/wiki/Property:P1059) | CVR number |  |
| `ee_registrikood` | [P6518](https://www.wikidata.org/wiki/Property:P6518) | Business Registry code (Estonia) |  |
| `kvk` | [P3220](https://www.wikidata.org/wiki/Property:P3220) | KvK company ID |  |
| `seorgnumber` | [P6460](https://www.wikidata.org/wiki/Property:P6460) | Swedish Organization Number | regexp, description, examples |
| `chuid` | [P4829](https://www.wikidata.org/wiki/Property:P4829) | Swiss Enterprise Identification Number |  |
| `auabn` | [P3548](https://www.wikidata.org/wiki/Property:P3548) | Australian Business Number | regexp, examples |
| `abn` | [P3548](https://www.wikidata.org/wiki/Property:P3548) | Australian Business Number | examples |
| `auacn` | [P3549](https://www.wikidata.org/wiki/Property:P3549) | Australian Company Number | regexp, examples |
| `be_vat` | [P3376](https://www.wikidata.org/wiki/Property:P3376) | enterprise number (Belgium) |  |
| `idnpwp` | [P8346](https://www.wikidata.org/wiki/Property:P8346) | Nomor Pokok Wajib Pajak | regexp, description |
| `cabn` | [P8860](https://www.wikidata.org/wiki/Property:P8860) | Canada Business Number |  |
| `il_hp` | [P10889](https://www.wikidata.org/wiki/Property:P10889) | Israeli Company Number |  |
| `cnpj` | [P6204](https://www.wikidata.org/wiki/Property:P6204) | CNPJ | regexp, examples |
| `fi_ytunnus` | [P12980](https://www.wikidata.org/wiki/Property:P12980) | Finnish Business ID |  |
| `ukgsscode` | [P836](https://www.wikidata.org/wiki/Property:P836) | GSS code (2011) | regexp, examples |
| `scopusauthoirid` | [P1153](https://www.wikidata.org/wiki/Property:P1153) | Scopus author ID | regexp |
| `snomedcode` | [P5806](https://www.wikidata.org/wiki/Property:P5806) | SNOMED CT ID | regexp, description, examples |
| `youtubevideoid` | [P1651](https://www.wikidata.org/wiki/Property:P1651) | YouTube video ID | regexp, description, examples |
| `mmsi` | [P587](https://www.wikidata.org/wiki/Property:P587) | MMSI |  |
| `ukurn` | [P2253](https://www.wikidata.org/wiki/Property:P2253) | DfE URN | regexp, description, examples |
| `ukprn` | [P4971](https://www.wikidata.org/wiki/Property:P4971) | UK Provider Reference Number | regexp, description, examples |
| `ifsc` | [P4635](https://www.wikidata.org/wiki/Property:P4635) | Indian Financial System Code | regexp, description, examples |
| `ncesid` | [P2484](https://www.wikidata.org/wiki/Property:P2484) | NCES school ID | regexp, description, examples |
| `usnpi` | [P9450](https://www.wikidata.org/wiki/Property:P9450) | National Provider Identifier | regexp, examples |
| `npi` | [P9450](https://www.wikidata.org/wiki/Property:P9450) | National Provider Identifier | regexp, examples |


### Records added by the ORG-ID.guide review

The ORG-ID.guide review (#17) added these records while this change was open.
This change keeps their ids, names and descriptions and adds the Wikidata
mapping, the Wikidata link, examples of named organizations and, where the
record had none, the regexp tested against Wikidata values.

| Record | Property | Wikidata label |
|---|---|---|
| `bg_eik` | [P8894](https://www.wikidata.org/wiki/Property:P8894) | BG EIK |
| `cz_ico` | [P4156](https://www.wikidata.org/wiki/Property:P4156) | Czech Registration ID (IČO) |
| `gb_nhs_ods_code` | [P9372](https://www.wikidata.org/wiki/Property:P9372) | NHS Organisation Data Service ID |
| `hu_company_registration_number` | [P2619](https://www.wikidata.org/wiki/Property:P2619) | Hungarian company ID |
| `ie_cro_number` | [P9679](https://www.wikidata.org/wiki/Property:P9679) | Companies Registration Office (Ireland) Registration Number |
| `lv_registration_number` | [P8053](https://www.wikidata.org/wiki/Property:P8053) | Latvian unified registration number |
| `nz_nzbn` | [P5687](https://www.wikidata.org/wiki/Property:P5687) | New Zealand Business Number |
| `permid` | [P3347](https://www.wikidata.org/wiki/Property:P3347) | PermID |
| `sk_ico` | [P8174](https://www.wikidata.org/wiki/Property:P8174) | Slovak Registration ID |
| `ua_edrpou` | [P3125](https://www.wikidata.org/wiki/Property:P3125) | EDRPOU code |

The opendata.mkrf.ru analysis added `ru_egrokn_regnum` (EGROKN registration
number) at the same time; it already maps to P5381. This change adds two
Wikidata examples to it instead of a second record.

The review of identifiers from Wikipedia
([#18](https://github.com/apicrafter/metacrafter-registry/issues/18)) added
`unspsc`, `us_ndc`, `gnd_id`, `lccn` and `handle_id` at the same time, with the
same Wikidata mappings (`us_ndc` has none). This change keeps those records, adds
two examples to `gnd_id`, and makes `lcnaf_id` a child of `lccn`: a Library of
Congress authority ID is the LCCN of an authority record.

### Corrected regexps

Wikidata values showed that these regexps were wrong. "Matches" counts the
Wikidata values that the regexp accepts, before and after.

| Record | Old regexp | New regexp | Matches before | Matches after | Cause |
|---|---|---|---:|---:|---|
| `seorgnumber` | `^[0-9]{9}$` | `^\d{6}-?\d{4}$` | 0/3000 | 2988/3000 | a Swedish organisation number has 10 digits |
| `usein` | `[0-9]{9}` | `^\d{2}-?\d{7}$` | 8/3000 | 2999/3000 | an EIN is written NN-NNNNNNN |
| `auabn` | `\d{2}\s\d{3}\s\d{3}\s\d{3}` | `^\d{2} ?\d{3} ?\d{3} ?\d{3}$` | 1/3000 | 2987/3000 | spaces were required |
| `auacn` | `\d{3}\s\d{3}\s\d{3}` | `^\d{3} ?\d{3} ?\d{3}$` | 2/531 | 531/531 | spaces were required |
| `idnpwp` | `^\d{2}\.\d{3}\.\d{3}\.\d-\d{3}\.\d{3}$` | adds `\d{15}` and `\d{16}` | 2/1126 | 1125/1126 | the NPWP has had 16 digits since 2024 |
| `cnpj` | punctuation required | punctuation optional | 2476/2812 | 2676/2812 | CNPJs are often written without punctuation |
| `openalexid` | `[ACIVW][1-9]\d{3,9}` | `^[ACFIPSTVWacfipstvw][1-9]\d{3,9}$` | 1614/3000 | 2999/3000 | sources, publishers, funders and topics were missing |
| `dcid` | `[A-Za-z\d_/]+` | `^[A-Za-z0-9_/.-]+$` | 2998/3000 | 3000/3000 | anchored; dots and hyphens occur |

`seorgnumber`, `idnpwp`, `ifsc`, `ncesid`, `ukurn`, `ukprn`, `snomedcode` and
`youtubevideoid` also got a real description instead of a generated stub.

### Records that were mapped already

| Record | Property | Added |
|---|---|---|
| `okato` | P721 | regexp `^(?:\d{2}\|\d{5}\|\d{8}\|\d{11})$`, examples |
| `doi` | P356 | regexp `^10\.\d{4,9}/\S+$`, examples |
| `doiprefix` | P1662 | regexp `^10(?:\.[1-9]\d*)+$`, examples |
| `eidr` | P2704 | regexp |
| `dcid` | P10730 | examples |
| `openalexid` | P10283 | description, examples |
| `github_username`, `instagram_username`, `twitter_username` | P2037, P2003, P2002 | examples of organization accounts |

## New records

92 new records, all `status: draft`. "Uses" is the number of Wikidata
statements with the property; "Matches" is the share of up to 3,000 Wikidata values that
the record regexp accepts.

### Codes and standards

| Record | Property | Wikidata label | Uses | Matches |
|---|---|---|---:|---:|
| `iso639_3` | [P220](https://www.wikidata.org/wiki/Property:P220) | ISO 639-3 code | 8,705 | 3000/3000 |
| `iso15924` | [P506](https://www.wikidata.org/wiki/Property:P506) | ISO 15924 alpha-4 code | 280 | 274/274 |
| `un_number` | [P695](https://www.wikidata.org/wiki/Property:P695) | UN number | 524 | 524/524 |
| `e_number` | [P628](https://www.wikidata.org/wiki/Property:P628) | E number | 622 | 615/620 |
| `hasc` | [P8119](https://www.wikidata.org/wiki/Property:P8119) | HASC | 11,096 | 3000/3000 |
| `ioc_country_code` | [P984](https://www.wikidata.org/wiki/Property:P984) | IOC country code | 265 | 254/254 |
| `fips10_4` | [P901](https://www.wikidata.org/wiki/Property:P901) | FIPS 10-4 (countries and regions) | 4,350 | 3000/3000 |
| `sec_cik` | [P5531](https://www.wikidata.org/wiki/Property:P5531) | Central Index Key | 3,783 | 3000/3000 |

### Medicine and life sciences

| Record | Property | Wikidata label | Uses | Matches |
|---|---|---|---:|---:|
| `icd10cm` | [P4229](https://www.wikidata.org/wiki/Property:P4229) | ICD-10-CM | 10,679 | 2969/3000 |
| `icd11` | [P7329](https://www.wikidata.org/wiki/Property:P7329) | ICD-11 ID (MMS) | 8,202 | 2990/3000 |
| `icd_o` | [P563](https://www.wikidata.org/wiki/Property:P563) | ICD-O | 1,064 | 995/1057 |
| `loinc` | [P4338](https://www.wikidata.org/wiki/Property:P4338) | LOINC ID | 373 | 366/372 |
| `mesh_descriptor_id` | [P486](https://www.wikidata.org/wiki/Property:P486) | MeSH descriptor ID | 39,602 | 3000/3000 |
| `mesh_tree_number` | [P672](https://www.wikidata.org/wiki/Property:P672) | MeSH tree code | 65,222 | 2999/3000 |
| `umls_cui` | [P2892](https://www.wikidata.org/wiki/Property:P2892) | UMLS CUI | 743,419 | 2956/3000 |
| `omim_id` | [P492](https://www.wikidata.org/wiki/Property:P492) | OMIM ID | 27,088 | 3000/3000 |
| `orphacode` | [P1550](https://www.wikidata.org/wiki/Property:P1550) | Orphanet ID | 9,696 | 3000/3000 |
| `doid` | [P699](https://www.wikidata.org/wiki/Property:P699) | Disease Ontology ID | 13,415 | 2997/3000 |
| `go_id` | [P686](https://www.wikidata.org/wiki/Property:P686) | Gene Ontology ID | 44,150 | 3000/3000 |
| `chebi_id` | [P683](https://www.wikidata.org/wiki/Property:P683) | ChEBI ID | 158,926 | 3000/3000 |
| `chembl_id` | [P592](https://www.wikidata.org/wiki/Property:P592) | ChEMBL ID | 50,443 | 3000/3000 |
| `chemspider_id` | [P661](https://www.wikidata.org/wiki/Property:P661) | ChemSpider ID | 129,474 | 3000/3000 |
| `pubchem_cid` | [P662](https://www.wikidata.org/wiki/Property:P662) | PubChem CID | 1,376,880 | 3000/3000 |
| `echa_infocard_id` | [P2566](https://www.wikidata.org/wiki/Property:P2566) | ECHA Substance Infocard ID | 56,547 | 3000/3000 |
| `ec_enzyme_number` | [P591](https://www.wikidata.org/wiki/Property:P591) | EC enzyme number | 14,961 | 2980/3000 |
| `ncbi_taxon_id` | [P685](https://www.wikidata.org/wiki/Property:P685) | NCBI taxonomy ID | 628,147 | 3000/3000 |
| `gbif_taxon_id` | [P846](https://www.wikidata.org/wiki/Property:P846) | GBIF-species-ID (before 2026 update) | 3,327,222 | 3000/3000 |
| `itis_tsn` | [P815](https://www.wikidata.org/wiki/Property:P815) | ITIS TSN | 665,108 | 3000/3000 |
| `cellosaurus_id` | [P3289](https://www.wikidata.org/wiki/Property:P3289) | Cellosaurus ID | 153,631 | 3000/3000 |
| `hmdb_id` | [P2057](https://www.wikidata.org/wiki/Property:P2057) | Human Metabolome Database ID | 47,112 | 2997/3000 |
| `nct_number` | [P3098](https://www.wikidata.org/wiki/Property:P3098) | ClinicalTrials.gov ID | 391,577 | 3000/3000 |

### Scholarly works, libraries, media

| Record | Property | Wikidata label | Uses | Matches |
|---|---|---|---:|---:|
| `pmid` | [P698](https://www.wikidata.org/wiki/Property:P698) | PubMed publication ID | 32,400,169 | 2975/3000 |
| `pmcid` | [P932](https://www.wikidata.org/wiki/Property:P932) | PMC publication ID | 6,615,786 | 3000/3000 |
| `arxiv_id` | [P818](https://www.wikidata.org/wiki/Property:P818) | arXiv ID | 465,225 | 387/392 |
| `issn_l` | [P7363](https://www.wikidata.org/wiki/Property:P7363) | ISSN-L | 148,308 | 3000/3000 |
| `lcnaf_id` | [P244](https://www.wikidata.org/wiki/Property:P244) | Library of Congress Authorities ID | 1,774,868 | 3000/3000 |
| `bnf_id` | [P268](https://www.wikidata.org/wiki/Property:P268) | Bibliothèque nationale de France ID | 788,534 | 3000/3000 |
| `scopus_source_id` | [P1156](https://www.wikidata.org/wiki/Property:P1156) | Scopus source ID | 46,167 | 3000/3000 |
| `nlm_unique_id` | [P1055](https://www.wikidata.org/wiki/Property:P1055) | NLM Unique ID | 35,821 | 2990/3000 |
| `freebase_mid` | [P646](https://www.wikidata.org/wiki/Property:P646) | Freebase ID | 4,470,735 | 2995/3000 |
| `google_kg_id` | [P2671](https://www.wikidata.org/wiki/Property:P2671) | Google Knowledge Graph ID | 8,182,547 | 3000/3000 |
| `imdb_id` | [P345](https://www.wikidata.org/wiki/Property:P345) | IMDb ID | 1,219,549 | 3000/3000 |
| `ringgold_id` | [P3500](https://www.wikidata.org/wiki/Property:P3500) | Ringgold ID | 107,783 | 3000/3000 |

### European Union

| Record | Property | Wikidata label | Uses | Matches |
|---|---|---|---:|---:|
| `eu_celex` | [P476](https://www.wikidata.org/wiki/Property:P476) | CELEX number | 5,019 | 3000/3000 |
| `eu_transparency_register_id` | [P2657](https://www.wikidata.org/wiki/Property:P2657) | EU Transparency Register ID | 16,649 | 3000/3000 |
| `eu_natura2000_site` | [P3425](https://www.wikidata.org/wiki/Property:P3425) | Natura 2000 site ID | 26,853 | 3000/3000 |

### Places

| Record | Property | Wikidata label | Uses | Matches |
|---|---|---|---:|---:|
| `gns_ufi` | [P2326](https://www.wikidata.org/wiki/Property:P2326) | GNS Unique Feature ID | 2,117,463 | 3000/3000 |
| `whosonfirst_id` | [P6766](https://www.wikidata.org/wiki/Property:P6766) | Who's on First ID | 585,300 | 2999/3000 |
| `ocd_division_id` | [P8651](https://www.wikidata.org/wiki/Property:P8651) | Open Civic Data Division ID | 6,153 | 3000/3000 |

### Russia and other former Soviet countries

| Record | Property | Wikidata label | Uses | Matches |
|---|---|---|---:|---:|
| `ru_esr_code` | [P2815](https://www.wikidata.org/wiki/Property:P2815) | ESR station code | 14,201 | 3000/3000 |
| `ru_gkgn_id` | [P1397](https://www.wikidata.org/wiki/Property:P1397) | State Catalogue of Geographical Names (Russia) ID | 67,649 | 3000/3000 |
| `ru_gvr_code` | [P884](https://www.wikidata.org/wiki/Property:P884) | State Water Register Code (Russia) | 39,320 | 3000/3000 |
| `ua_katottg` | [P9435](https://www.wikidata.org/wiki/Property:P9435) | KATOTTH ID | 31,981 | 3000/3000 |
| `ua_koatuu` | [P1077](https://www.wikidata.org/wiki/Property:P1077) | KOATUU ID | 41,393 | 3000/3000 |
| `by_soato` | [P2672](https://www.wikidata.org/wiki/Property:P2672) | SOATO ID | 22,902 | 3000/3000 |
| `kz_kato` | [P4838](https://www.wikidata.org/wiki/Property:P4838) | CATO ID | 9,666 | 3000/3000 |

### Administrative units by country

| Record | Property | Wikidata label | Uses | Matches |
|---|---|---|---:|---:|
| `de_ags` | [P439](https://www.wikidata.org/wiki/Property:P439) | German municipality key | 11,613 | 3000/3000 |
| `de_kreisschluessel` | [P440](https://www.wikidata.org/wiki/Property:P440) | German district key | 734 | 733/733 |
| `de_ars` | [P1388](https://www.wikidata.org/wiki/Property:P1388) | German regional key | 12,377 | 3000/3000 |
| `it_istat_comune` | [P635](https://www.wikidata.org/wiki/Property:P635) | ISTAT ID | 8,817 | 2994/3000 |
| `it_codice_catastale` | [P806](https://www.wikidata.org/wiki/Property:P806) | Italian cadastre code (municipality) | 8,972 | 2996/3000 |
| `es_ine_municipio` | [P772](https://www.wikidata.org/wiki/Property:P772) | INE code | 38,596 | 2999/3000 |
| `ch_bfs_gemeinde` | [P771](https://www.wikidata.org/wiki/Property:P771) | Swiss municipality code | 3,401 | 3000/3000 |
| `at_gkz` | [P964](https://www.wikidata.org/wiki/Property:P964) | Austrian municipality key | 2,604 | 2467/2467 |
| `pl_teryt_terc` | [P1653](https://www.wikidata.org/wiki/Property:P1653) | TERC municipality code | 3,614 | 2851/3000 |
| `pl_teryt_simc` | [P4046](https://www.wikidata.org/wiki/Property:P4046) | SIMC place ID | 65,662 | 2992/3000 |
| `ro_siruta` | [P843](https://www.wikidata.org/wiki/Property:P843) | SIRUTA code | 16,978 | 3000/3000 |
| `jp_lg_code` | [P429](https://www.wikidata.org/wiki/Property:P429) | dantai code | 1,984 | 1981/1981 |
| `se_kommunkod` | [P525](https://www.wikidata.org/wiki/Property:P525) | Swedish municipality code | 1,461 | 1453/1453 |
| `no_kommunenummer` | [P2504](https://www.wikidata.org/wiki/Property:P2504) | Norwegian municipality number | 1,311 | 1048/1048 |
| `fi_kuntanumero` | [P1203](https://www.wikidata.org/wiki/Property:P1203) | Finnish municipality number | 625 | 621/621 |
| `dk_kommunekode` | [P1168](https://www.wikidata.org/wiki/Property:P1168) | municipality code (Denmark) | 347 | 345/346 |
| `hu_ksh_code` | [P939](https://www.wikidata.org/wiki/Property:P939) | KSH code | 3,180 | 3000/3000 |
| `be_nis_code` | [P1567](https://www.wikidata.org/wiki/Property:P1567) | NIS/INS code | 2,960 | 2960/2960 |
| `bg_ekatte` | [P3990](https://www.wikidata.org/wiki/Property:P3990) | BG EKATTE place ID | 11,018 | 3000/3000 |
| `ph_psgc` | [P988](https://www.wikidata.org/wiki/Property:P988) | Philippine Standard Geographic Code | 8,684 | 3000/3000 |
| `cn_division_code` | [P442](https://www.wikidata.org/wiki/Property:P442) | China division code for Statistics | 753,669 | 2995/3000 |
| `id_kode_wilayah` | [P2588](https://www.wikidata.org/wiki/Property:P2588) | administrative code of Indonesia | 109,967 | 3000/3000 |
| `mx_inegi_locality` | [P1976](https://www.wikidata.org/wiki/Property:P1976) | INEGI locality ID | 204,290 | 3000/3000 |
| `fr_uai` | [P3202](https://www.wikidata.org/wiki/Property:P3202) | UAI code | 66,910 | 3000/3000 |

### Company registers

| Record | Property | Wikidata label | Uses | Matches |
|---|---|---|---:|---:|
| `cn_uscc` | [P6795](https://www.wikidata.org/wiki/Property:P6795) | Unified Social Credit ID | 2,706 | 2666/2690 |
| `sg_uen` | [P13194](https://www.wikidata.org/wiki/Property:P13194) | Singapore Unique Entity Number | 450 | 451/452 |
| `at_firmenbuchnummer` | [P5285](https://www.wikidata.org/wiki/Property:P5285) | Firmenbuchnummer | 446 | 440/446 |
| `kr_crn` | [P6859](https://www.wikidata.org/wiki/Property:P6859) | Corporate Number (South Korea) | 91 | 95/96 |

### Online accounts

| Record | Property | Wikidata label | Uses | Matches |
|---|---|---|---:|---:|
| `facebook_username` | [P2013](https://www.wikidata.org/wiki/Property:P2013) | Facebook username | 431,758 | no regexp |
| `youtube_channel_id` | [P2397](https://www.wikidata.org/wiki/Property:P2397) | YouTube channel ID | 159,334 | 3000/3000 |
| `linkedin_company_id` | [P4264](https://www.wikidata.org/wiki/Property:P4264) | LinkedIn company or organization ID | 53,092 | 2835/3000 |
| `telegram_username` | [P3789](https://www.wikidata.org/wiki/Property:P3789) | Telegram username | 11,291 | 2956/3000 |
| `vk_username` | [P3185](https://www.wikidata.org/wiki/Property:P3185) | VK username | 14,716 | 2975/3000 |
| `tiktok_username` | [P7085](https://www.wikidata.org/wiki/Property:P7085) | TikTok username | 40,609 | 2999/3000 |
| `mastodon_address` | [P4033](https://www.wikidata.org/wiki/Property:P4033) | Mastodon address | 13,091 | 2978/3000 |
| `bluesky_handle` | [P12361](https://www.wikidata.org/wiki/Property:P12361) | Bluesky handle | 11,419 | 2986/3000 |


Notes:

- `facebook_username` has no regexp. Wikidata stores page names with any
  letters, dots and hyphens, so a regexp would accept almost any word.
- `gbif_taxon_id` is the numeric key of the GBIF Backbone Taxonomy (P846).
  Wikidata keeps the taxon IDs of the taxonomy that GBIF introduced in 2026 in
  P14607. A record for them can follow when datasets start to use them.
- `pmcid` accepts the number with or without the `PMC` prefix; Wikidata stores
  it without.
- `cn_division_code` accepts the code with or without the spaces that
  Wikidata puts between its groups.
- `icd10cm` leaves out the chapter ranges (such as `A00-Z99`) that Wikidata
  also stores; `icd11` covers stem codes and extension codes.
- The 8 online account records name only organization accounts in their
  examples.

## Mappings to other property types

These records map to Wikidata properties that are not external identifiers.
The mappings are kept: the record holds the values of the property.

- Strings: `aircraftnumber` (P426), `colorhextriplet` and `hexcolor` (P465),
  `ec_enzyme_number` (P591, new), `faalid` (P240), `fccid` (P7290),
  `file_extension` (P1195), `flightnumber` (P3090), `iataairlinecode` (P229),
  `iataairportcode` (P238), `icaoairlinecode` (P230), `icaoairportcode` (P239),
  `ipv4subnet` (P3761), `ipv6subnet` (P3793), `isicrev4` (P1796), `mimetype`
  (P1163), `molformula` (P274), `ncitcode` (P1748), `phone` (P1329), `postindex`
  (P281), `skype_username` (P2893), `tickersymbol` (P249), `unclass` (P874),
  `unpkggroup` (P876).
- Items: `birthplace` (P19), `brand` (P1716), `color` (P462), `continent`
  (P30), `genre` (P136), `honorificprefix` (P511), `industry` (P452),
  `namesuffix` (P1035), `programminglang` (P277), `religion` (P140).
- Quantities: `datasize` and `filesize` (P3575), `elevation` (P2044),
  `temperature` (P2076), `utctimezoneoffset` (P2907), `weight` (P2067).
- Other: `name` (P2561, monolingual text), `url` (P2699, URL).

## Not done

- **`us_ndc`.** P3640 (National Drug Code) stores the labeler and product
  segments only, such as `0009-0417`. The record is the full package code with
  three segments and rejects that form, so it is not mapped.
- **`gtin` and `ean`.** `gtin` is the GS1 element string with Application
  Identifier (01): `01` and 14 digits. P3962 (Global Trade Item Number) holds
  the plain GTIN of 8 to 14 digits. The values differ, so `gtin` is not
  mapped. `ean` accepts 13 digits only, which is narrower than P3962.
- **`ensembl_id`.** The record covers gene, transcript and protein IDs;
  Wikidata has one property for each (P594, P704, P705). `ensemblgeneid`
  already maps to P594.
- **Person identifiers.** Authority files of people (1,713 properties),
  Google Scholar author ID (P1960), LinkedIn personal profile (P6634) and
  similar properties identify people. The registry already has ORCID, ISNI,
  VIAF and Scopus author ID; others need examples that are not personal data.
- **Candidates for a next round**, from the script report (most used first):
  - taxa: Catalogue of Life ID (P10585), Open Tree of Life ID (P9157), IRMNG
    (P5055), Encyclopedia of Life (P830), World Flora Online (P7715), IPNI
    (P961), iNaturalist taxon (P3151), WoRMS (P850), GBIF taxon ID after 2026
    (P14607);
  - life sciences: RefSeq protein and RNA IDs (P637, P639), Ensembl transcript
    and protein IDs (P704, P705), UniChem (P11089), SureChEMBL (P2877), KEGG
    (P665), LIPID MAPS (P2063), InterPro (P2926), Reactome (P3937);
  - scholarly works: Dimensions (P6179), DBLP (P8978), zbMATH Open (P894),
    JSTOR (P888), CiNii Research (P11496), Crossref journal ID (P8375);
  - schools: INEP (Brazil, P11704), NPSN (Indonesia, P4128), U-DISE (India,
    P6391), Italian school ID (P5114), MEXT school code (Japan, P11127);
  - places: INSPIRE ID (P4115), Common Database on Designated Areas (P4762),
    EU surface water body code (P2856), GADM ID (P8714), INSEE canton and
    arrondissement codes (P2506, P3423), Australian Statistical Geography
    (P10112), LGD codes of India (P12745 and others);
  - companies: German register number (P12012), Cyprus company ID (P14388),
    Malaysian company numbers (P6843, P12530), Canadian corporation number
    (P13850), Crunchbase organization ID (P2088), OpenSanctions ID (P10632);
  - classifications: US SIC code (P3242), ANZSRC fields of research (P8529),
    Mathematics Subject Classification (P3285), FoodEx2 (P4637), ICD-10-PCS
    (P1690);
  - media: MusicBrainz artist, release group and work IDs (P434, P436, P435),
    Kinopoisk film ID (P2603).
- **Sync tool.** Issue #21 asks for a command that keeps names, descriptions,
  examples and regexps in step with Wikidata. `scripts/wikidata_properties.py`
  reports the differences; it does not change records.

## Reproduce

```bash
python scripts/wikidata_properties.py fetch          # writes wikidata_properties.json (~15 MB)
python scripts/wikidata_properties.py report > wikidata_report.md
python scripts/wikidata_properties.py report --class Q42396390 --limit 100   # one Wikidata class
```

The report lists (1) mappings to properties that are not external identifiers,
(2) mapped records that lack a regexp or examples that Wikidata has, and
Wikidata examples that do not match the record regexp, and (3) the most used
unmapped properties of selected Wikidata classes. The Wikidata Query Service
limits request rates; `fetch` retries after HTTP 429 and 5xx answers.
