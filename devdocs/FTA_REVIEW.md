# FTA (Fast Text Analysis) semantic types: review (2026-11-04)

Issue: [apicrafter/metacrafter-registry#38](https://github.com/apicrafter/metacrafter-registry/issues/38).

The issue asks to:

1. review the semantic types of FTA and add the missing ones to the registry;
2. add a mapping table from FTA semantic types to registry ids;
3. add FTA to the list of tools.

Source reviewed: [tsegall/fta](https://github.com/tsegall/fta) by Tim Segall
at commit `51b3dd046f4a25379a483960619fe712d3dccc55` (2026-06-12). The
repository is licensed Apache-2.0. The list of types is
`types/src/main/resources/reference/plugins.json`, and `SemanticTypes.md`
documents the same 258 types. The list in the issue (2022) had about 100
types; FTA has grown since, so this review uses the current list. All numbers
below were computed from that commit.

## Summary

- FTA defines **258 semantic types**. Many are one concept in several
  languages or countries: `COLOR.TEXT_<lang>` exists for 15 languages,
  `POSTAL_CODE.POSTAL_CODE_<country>` for 25 countries.
- **Done in this change:**
  - New crosswalk key `mappings.fta`. It holds FTA semantic types as FTA
    documents them. The schema accepts only FTA's form (uppercase segments,
    optional `<LANGUAGE>`, `<COUNTRY>` or `<LOCALE>` placeholder) and rejects
    values such as `email`.
  - **254 FTA types are mapped to 180 registry records**: 160 types to 107
    existing records and 94 types to 73 new ones. A record can carry several
    FTA types (`color` carries the 15 `COLOR.TEXT_*` types); an FTA type maps
    to at most one record (a test checks this).
  - **73 new draft records**: 21 value types, 18 postal code patterns and 34
    administrative divisions. Countries TZ (Tanzania) and UY (Uruguay) are
    added to `data/countries.yaml`.
  - New tool `fta` (`data/tools/detectors/fta.yaml`). Its `supported_types`
    are the records that carry `mappings.fta`; a test keeps them in step.
  - `crosswalk("fta", ...)` resolves names that FTA binds to a locale at run
    time, see [Locale-bound types](#locale-bound-types).
- **Not mapped (4 types):** `CHECKDIGIT.LUHN`, `FREE_TEXT`,
  `STATE_PROVINCE.STATE_PROVINCE_NA` and
  `STATE_PROVINCE.STATE_PROVINCE_NAME_NA`. See [Not mapped](#not-mapped).

| Group | FTA types | To existing records | To new records | Not mapped |
|---|---|---|---|---|
| Identifiers and check digits (`IDENTITY.*`, `CHECKDIGIT.*`, `SSN`) | 23 | 22 | 0 | 1 |
| Postal codes (`POSTAL_CODE.*`) | 27 | 9 | 18 | 0 |
| Administrative divisions (`STATE_PROVINCE.*`) | 53 | 17 | 34 | 2 |
| Localized names (`*.TEXT_<lang>`, `GENDER`, `NATIONALITY`, `HONORIFIC`, `JOB_TITLE`, `INDUSTRY`, `MARITAL_STATUS`) | 78 | 57 | 21 | 0 |
| Other value types | 77 | 55 | 21 | 1 |
| **Total** | **258** | **160** | **94** | **4** |

## What FTA is

FTA is a Java library that profiles a stream of values, such as a column of a
CSV file. It infers the base type (long, double, string, date), the format as
a regular expression and, when it can, a semantic type. It uses the values,
the column name and the locale of the analysis. Each semantic type is a
plugin of one of three kinds: a regular expression, a list of valid values
(for example the 26 Swiss canton codes), or Java code (for example the check
digit of a VAT number).

FTA and the registry describe the same thing, what a value means, so most FTA
types match a registry record one to one.

## Locale-bound types

Some FTA types are written with a placeholder that FTA fills from the locale
of the analysis:

- `<LANGUAGE>`: `GENDER.TEXT_<LANGUAGE>` becomes `GENDER.TEXT_DE` for a German
  locale. Also `STREET_ADDRESS_<LANGUAGE>` and `STREET_NAME_BARE_<LANGUAGE>`.
- `<LOCALE>`: `MONTH.FULL_<LOCALE>` becomes `MONTH.FULL_fr-FR`. Also
  `MONTH.ABBR_`, `DAY.FULL_` and `DAY.ABBR_`.
- `<COUNTRY>`: `IDENTITY.VAT_<COUNTRY>` becomes `IDENTITY.VAT_IT`.

`mappings.fta` keeps the placeholder, because all bound names have one
meaning (`GENDER.TEXT_<LANGUAGE>` is always a gender). The exception is
`IDENTITY.VAT_<COUNTRY>`: each country's VAT number is a different registry
record, so the eight bound names that FTA supports are mapped instead
(`IDENTITY.VAT_AT`, `_ES`, `_FR`, `_GB`, `_UK`, `_IT`, `_NL`, `_PL`). FTA
binds the `en-UK` locale to `UK`, so both `_GB` and `_UK` are listed.

`crosswalk("fta", name)` first looks for the exact name. If no record has it,
it replaces the part after the last underscore with each placeholder and
looks again. So `MONTH.FULL_fr-FR` finds `month`, `GENDER.TEXT_DE` finds
`gender`, and `STREET_ADDRESS_JA` (an FTA type of its own) still finds
`address` and not `street_address`.

## New records

All new records are `status: draft`. Each one has a description in our own
words, examples, a negative example where it has a regexp, a Wikipedia link
where one exists, a link to FTA's `SemanticTypes.md` and a Russian name.
Regexps of codes and postal codes follow the published format and agree with
FTA's own regexp or value list. Example values of place names and codes were
checked against FTA's reference lists; Wikidata properties were checked
against Wikidata.

**Value types (21):**

| Id | FTA types | Notes |
|---|---|---|
| `easting`, `northing` | `COORDINATE.EASTING`, `COORDINATE.NORTHING` | Projected coordinates, for example British National Grid metres. |
| `payment_card_brand` | `CREDIT_CARD_TYPE` | VISA, Mastercard, AMEX. The card number stays `bankcard`. |
| `cryptocurrency` | `CRYPTOCURRENCY.TEXT_EN`, `_JA` | Name of a cryptocurrency. |
| `cardinal_direction` | `DIRECTION` | N, SW, Northeast, Westbound. |
| `file_extension` | `FILENAME_EXT` | Wikidata P1195. |
| `industry` | `INDUSTRY_EN`, `INDUSTRY_JA` | Name of an industry; codes stay `naicscode`, `isicrev4`, `eu_nace`. Wikidata P452. |
| `language`, with patterns `iso639_1` and `iso639_2` | `LANGUAGE.TEXT_*` (15), `LANGUAGE.ISO-639-1`, `LANGUAGE.ISO-639-2` | The registry had `languagetag` (BCP 47) but no language datatype. Patterns map to Wikidata P218 and P219. |
| `half_year` | `PERIOD.HALF` | H1, H2. |
| `year_range` | `PERIOD.YEAR_RANGE` | 2019-2020. |
| `age_range` | `PERSON.AGE_RANGE` | 18-24, 65+. Parent `age`. |
| `marital_status` | `PERSON.MARITAL_STATUS_EN`, `_JA` | PII. |
| `race_ethnicity` | `PERSON.RACE_EN`, `PERSON.RACE_ABBR_EN` | PII, a GDPR special category. |
| `birth_year` | `PERSON.YEAR_OF_BIRTH` | PII. Parent `year`. |
| `geojson`, `wkt` | `SPATIAL.GEOJSON`, `SPATIAL.WKT` | Geometry formats. |
| `street_address` | `STREET_ADDRESS_EN`, `STREET_ADDRESS_<LANGUAGE>` | House number and street. Schema.org `streetAddress`. |
| `address_line2` | `STREET_ADDRESS2_EN`, `3_EN`, `4_EN` | Apartment, suite, PO box. |
| `street_suffix` | `STREET_MARKER_EN` | St, Ave, Blvd. |

**Postal codes (18 patterns of `postindex`):** `at_postcode`,
`au_postcode`, `bg_postcode`, `br_postcode`, `ca_postcode`, `ch_postcode`,
`co_postcode`, `dk_postcode`, `fi_postcode`, `in_postcode`, `it_postcode`,
`jp_postcode`, `mx_postcode`, `no_postcode`, `pt_postcode`, `ro_postcode`,
`se_postcode`, `uy_postcode`. Germany, Spain, France, the Netherlands,
Poland, Russia, the UK and the US already had records.

**Administrative divisions (34):**

| Country | Names (datatypes) | Codes (patterns) |
|---|---|---|
| Australia | `au_state`, `au_suburb` | `au_state_code` |
| Brazil | `br_state`, `br_municipality` | `br_state_code`, `br_municipality_code` (IBGE, Wikidata P1585) |
| Colombia | `co_department`, `co_municipality` | |
| Ecuador | `ec_province` | |
| Germany | `de_state` | |
| Hungary | `hu_county` | |
| Ireland | `ie_county`, `ie_province` | |
| Italy | `it_region`, `it_province`, `it_comune` | `it_province_code` |
| Japan | `jp_region` | `jp_prefecture_code` (JIS X 0401), a pattern of the existing `prefecture` |
| Mexico | `mx_municipality` | |
| Netherlands | `nl_province`, `nl_municipality` | `nl_municipality_code` (CBS, Wikidata P382) |
| Peru | `pe_region`, `pe_province` | |
| Portugal | `pt_district` | |
| South Africa | `za_province` | `za_province_code` |
| Switzerland | `ch_canton` | `ch_canton_code` |
| Spain | `es_province` | |
| Tanzania | `tz_region` | |
| United Kingdom | `gb_county` | |

## Judgment calls

Where the registry had more than one candidate, or the match is not exact:

- `COLOR.HEX` maps to `hexcolor`. `colorhextriplet` describes the same
  values; the two patterns are near-duplicates.
- `CHECKDIGIT.ABA` maps to `abaroutingnum` (stable), not to the draft `aba`.
  `IDENTITY.NHS_UK` maps to `uknhsnum`, not to the draft `nhsnumber`.
  `CHECKDIGIT.EAN13` maps to `ean`, `CHECKDIGIT.ISBN` to `isbn13`.
- `GUID`, `MACADDRESS`, `HASH.SHA1_HEX`, `HASH.SHA256_HEX`, `SSN` and
  `IDENTITY.NI_UK` map to the canonical ids `uuid`, `mac_address`,
  `sha1hash`, `sha256hash`, `usssn` and `uknino`, not to their aliases.
- `EPOCH.SECONDS` and `EPOCH.MILLISECONDS` both map to `unixtime`: the same
  concept in two units. The `unixtime` regexp covers seconds only.
- `CURRENCY.TEXT_EN` maps to the pattern `iso4217curname`;
  `CURRENCY.TEXT_JA` maps to `currency`.
- `HONORIFIC_EN` maps to `honorificprefix`. `HONORIFIC_JA` (様, さん, 先生)
  maps to `namesuffix`: Japanese honorifics follow the name.
- `NAME.MIDDLE_INITIAL` maps to `person_midname` and `NAME.LAST_FIRST` to
  `person_fullname`: other forms of the same concept.
- `COORDINATE_PAIR.DECIMAL` and `_PAREN` map to `geopoint`;
  `COORDINATE.LATITUDE_DMS` to `latitude`.
- `STREET_ADDRESS_JA` maps to `address`: FTA's plugin detects a full
  Japanese address, with prefecture, city and block.
- `STREET_NUMBER` maps to `buildingnumber`.
- `POSTAL_CODE.POSTAL_CODE_MX` maps to the new `mx_postcode`, although
  `espostcode` lists MX among its countries. `espostcode` describes Spanish
  codes.
- `STATE_PROVINCE.PREFECTURE_ISO_JA` (`JP-13`) maps to the generic
  `iso3166code`. `STATE_PROVINCE.STATE_MX` holds ISO 3166-2:MX codes (`CMX`,
  `JAL`) and maps to `iso3166_mx3a`.
- `STATE_PROVINCE.STATE_US` and `STATE_NAME_US` both map to `usstate`, which
  holds a name or a code. `STATE_UNION_IN` and `STATE_UNION_NAME_IN` both map
  to `state` (India).

## Not mapped

| FTA type | Why |
|---|---|
| `CHECKDIGIT.LUHN` | A digit string with a valid Luhn check digit. It says how a value is checked, not what it means: card numbers, IMEI numbers and other identifiers all pass the check. |
| `FREE_TEXT` | Prose such as descriptions, notes or comments. It is a storage form, like D3M's `Text`, not a meaning. |
| `STATE_PROVINCE.STATE_PROVINCE_NA` | Union of US state, Canadian province and Mexican state codes. Each part is mapped through its own FTA type. |
| `STATE_PROVINCE.STATE_PROVINCE_NAME_NA` | The same union, for names. |

## Follow-ups (not done here)

- Near-duplicate records seen during the review: `hexcolor` and
  `colorhextriplet`, `aba` and `abaroutingnum`, `nhsnumber` and `uknhsnum`,
  `isbn` and `isbn13`. Merging them (with aliases) is a separate change.
- FTA validates check digits for ABA, CUSIP, SEDOL, ISIN, EAN-13, UPC, IBAN,
  VIN, NPI and several national identifiers. Records whose `checksum` field
  is missing could take FTA's algorithms as a reference.
- The `unixtime` regexp is not anchored and does not cover milliseconds.

## Mapping table (all 258 FTA types)

The description is FTA's own, from `plugins.json`. "(new)" marks a record
added in this change.

| FTA semantic type | FTA description | Registry id |
|---|---|---|
| `AIRLINE.IATA_CODE` | IATA Airline Code | `iataairlinecode` |
| `AIRLINE.TEXT_EN` | Airline Name | `airlinename` |
| `AIRPORT_CODE.IATA` | IATA Airport Code | `iataairportcode` |
| `CHECKDIGIT.ABA` | ABA Number (or Routing Transit Number (RTN)) | `abaroutingnum` |
| `CHECKDIGIT.CUSIP` | CUSIP - North American Security Identifiers | `cusip` |
| `CHECKDIGIT.EAN13` | EAN-13 - EAN-13/ISBN-13 Check digit | `ean` |
| `CHECKDIGIT.IBAN` | IBAN - International Bank Account Number | `iban` |
| `CHECKDIGIT.ISBN` | ISBN-13 identifiers (with hyphens) | `isbn13` |
| `CHECKDIGIT.ISIN` | ISIN - International Securities Identification Number | `isin` |
| `CHECKDIGIT.LUHN` | LUHN Checkdigit (Credit Cards, IMEI, etc) | not mapped |
| `CHECKDIGIT.SEDOL` | SEDOL - UK Security Identifiers | `sedol` |
| `CHECKDIGIT.UPC` | UPC - Universal Product Code | `upc` |
| `CITY` | City/Town | `city` |
| `COLOR.HEX` | Hex Color code | `hexcolor` |
| `COLOR.TEXT_CS` | Color name (Czech) | `color` |
| `COLOR.TEXT_DA` | Color name (Danish) | `color` |
| `COLOR.TEXT_DE` | Color name (German) | `color` |
| `COLOR.TEXT_EN` | Color name (English) | `color` |
| `COLOR.TEXT_ES` | Color name (Spanish) | `color` |
| `COLOR.TEXT_FI` | Color name (Finnish) | `color` |
| `COLOR.TEXT_FR` | Color name (French) | `color` |
| `COLOR.TEXT_IT` | Color name (Italian) | `color` |
| `COLOR.TEXT_JA` | Color name (Japanese) | `color` |
| `COLOR.TEXT_NL` | Color name (Dutch) | `color` |
| `COLOR.TEXT_PL` | Color name (Polish) | `color` |
| `COLOR.TEXT_PT` | Color name (Portuguese) | `color` |
| `COLOR.TEXT_RO` | Color name (Romanian) | `color` |
| `COLOR.TEXT_RU` | Color name (Russian) | `color` |
| `COLOR.TEXT_SV` | Color name (Swedish) | `color` |
| `COMPANY_NAME` | Organization/Company Name | `orgname` |
| `CONTINENT.CODE_EN` | Continent Code | `continentcode` |
| `CONTINENT.TEXT_CS` | Continent (Czech) | `continent` |
| `CONTINENT.TEXT_DA` | Continent (Danish) | `continent` |
| `CONTINENT.TEXT_DE` | Continent (German) | `continent` |
| `CONTINENT.TEXT_EN` | Continent | `continent` |
| `CONTINENT.TEXT_ES` | Continent (Spanish) | `continent` |
| `CONTINENT.TEXT_FI` | Continent (Finnish) | `continent` |
| `CONTINENT.TEXT_FR` | Continent (French) | `continent` |
| `CONTINENT.TEXT_IT` | Continent (Italian) | `continent` |
| `CONTINENT.TEXT_JA` | Continent (Japanese) | `continent` |
| `CONTINENT.TEXT_NL` | Continent (Dutch) | `continent` |
| `CONTINENT.TEXT_PL` | Continent (Polish) | `continent` |
| `CONTINENT.TEXT_PT` | Continent (Portuguese) | `continent` |
| `CONTINENT.TEXT_RO` | Continent (Romanian) | `continent` |
| `CONTINENT.TEXT_RU` | Continent (Russian) | `continent` |
| `CONTINENT.TEXT_SV` | Continent (Swedish) | `continent` |
| `COORDINATE.EASTING` | Latitude - easting | `easting` (new) |
| `COORDINATE.LATITUDE_DECIMAL` | Latitude (Decimal degrees) | `latitude` |
| `COORDINATE.LATITUDE_DMS` | Latitude (degrees/minutes/seconds) | `latitude` |
| `COORDINATE.LONGITUDE_DECIMAL` | Longitude (Decimal degrees) | `longitude` |
| `COORDINATE.LONGITUDE_DMS` | Longitude (degrees/minutes/seconds) | `longitude` |
| `COORDINATE.NORTHING` | Longitude - northing | `northing` (new) |
| `COORDINATE_PAIR.DECIMAL` | Coordinate Pair Lat,Long - Decimal degrees | `geopoint` |
| `COORDINATE_PAIR.DECIMAL_PAREN` | Coordinate Pair (Lat,Long) - Decimal degrees) | `geopoint` |
| `COUNTRY.ISO-3166-2` | Country as defined by ISO 3166 - Alpha 2 | `countrycode_alpha2` |
| `COUNTRY.ISO-3166-3` | Country as defined by ISO 3166 - Alpha 3 | `countrycode_alpha3` |
| `COUNTRY.TEXT_CS` | Country as a string (Czech) | `country` |
| `COUNTRY.TEXT_DA` | Country as a string (Danish) | `country` |
| `COUNTRY.TEXT_DE` | Country as a string (German) | `decountryname` |
| `COUNTRY.TEXT_EN` | Country as a string (English language) | `encountryname` |
| `COUNTRY.TEXT_ES` | Country as a string (Spanish) | `country` |
| `COUNTRY.TEXT_FI` | Country as a string (Finnish) | `country` |
| `COUNTRY.TEXT_FR` | Country as a string (French) | `country` |
| `COUNTRY.TEXT_IT` | Country as a string (Italian) | `country` |
| `COUNTRY.TEXT_JA` | Country as a string (Japanese) | `country` |
| `COUNTRY.TEXT_NL` | Country as a string (Dutch) | `country` |
| `COUNTRY.TEXT_PL` | Country as a string (Polish) | `country` |
| `COUNTRY.TEXT_PT` | Country as a string (Portuguese) | `country` |
| `COUNTRY.TEXT_RO` | Country as a string (Romanian) | `country` |
| `COUNTRY.TEXT_RU` | Country as a string (Russian) | `ruscountryname` |
| `COUNTRY.TEXT_SV` | Country as a string (Swedish) | `country` |
| `CREDIT_CARD_TYPE` | Type of Credit CARD - e.g. AMEX, VISA, ... | `payment_card_brand` (new) |
| `CRYPTOCURRENCY.TEXT_EN` | Cryptocurrency Name | `cryptocurrency` (new) |
| `CRYPTOCURRENCY.TEXT_JA` | Cryptocurrency Name (Japanese) | `cryptocurrency` (new) |
| `CURRENCY.TEXT_EN` | Currency Name | `iso4217curname` |
| `CURRENCY.TEXT_JA` | Currency Name (Japanese) | `currency` |
| `CURRENCY_CODE.ISO-4217` | Currency as defined by ISO 4217 | `iso4217curcode` |
| `DAY.ABBR_<LOCALE>` | Day of Week Abbreviation <LOCALE> = Locale, e.g. en-US for English language in US) | `dayofweek` |
| `DAY.DIGITS` | Numeric Day of Month | `dayofmonth` |
| `DAY.FULL_<LOCALE>` | Full Day of Week name <LOCALE> = Locale, e.g. en-US for English language in US) | `dayofweek` |
| `DIRECTION` | Cardinal Direction | `cardinal_direction` (new) |
| `EMAIL` | Email Address | `email` |
| `EPOCH.MILLISECONDS` | Unix Epoch (Timestamp) - milliseconds | `unixtime` |
| `EPOCH.SECONDS` | Unix Epoch (Timestamp) - seconds | `unixtime` |
| `FILENAME` | Name of file | `filename` |
| `FILENAME_EXT` | Filename extension | `file_extension` (new) |
| `FREE_TEXT` | Free Text field - e.g. Description, Notes, Comments, ... | not mapped |
| `FULL_ADDRESS_EN` | Full Address (English Language) | `address` |
| `GENDER.TEXT_<LANGUAGE>` | Gender | `gender` |
| `GENDER.TEXT_JA` | Gender (Japanese Language) | `gender` |
| `GENDER.TEXT_ZH` | Gender (Chinese Language) | `gender` |
| `GUID` | Globally Unique Identifier, e.g. 30DD879E-FE2F-11DB-8314-9800310C9A67 | `uuid` |
| `HASH.SHA1_HEX` | SHA1 Hash - hexadecimal | `sha1hash` |
| `HASH.SHA256_HEX` | SHA256 Hash - hexadecimal | `sha256hash` |
| `HONORIFIC_EN` | Honorific (English Language) | `honorificprefix` |
| `HONORIFIC_JA` | Honorific (Japanese Language) | `namesuffix` |
| `IDENTIFIER` | Unique Identifier | `id` |
| `IDENTITY.AADHAAR_IN` | Aadhaar (India) | `aadhaar` |
| `IDENTITY.BSN_NL` | BSN (Netherlands) | `bsn` |
| `IDENTITY.DUNS` | Data Universal Numbering System (Dun & Bradstreet) | `duns` |
| `IDENTITY.EIN_US` | Employer Identification Number (US) | `usein` |
| `IDENTITY.INDIVIDUAL_NUMBER_JA` | Individual Number / My Number (Japan) | `mynumber` |
| `IDENTITY.NHS_UK` | NHS (UK) | `uknhsnum` |
| `IDENTITY.NI_UK` | National Insurance Number (UK) | `uknino` |
| `IDENTITY.NPI_US` | National Provider Identifier (US) | `usnpi` |
| `IDENTITY.PERSONNUMMER_SE` | Personal identity number (Sweden) | `sepersonnummer` |
| `IDENTITY.SIN_CA` | Social Insurance Number | `casin` |
| `IDENTITY.SSN_CH` | AVH Number / SSN (Switzerland) | `chahv` |
| `IDENTITY.SSN_FR` | Social Security Number (France) | `frnir` |
| `IDENTITY.VAT_<COUNTRY>` | VAT | `AT`: `at_vat`, `ES`: `esvat`, `FR`: `frvat`, `GB`: `gb_vat`, `IT`: `it_iva`, `NL`: `nlbtw`, `PL`: `plnip`, `UK`: `gb_vat` |
| `IMEI` | International Mobile Equipment Identity | `imei` |
| `INDUSTRY_CODE.NAICS` | Industry Code - NAICS | `naicscode` |
| `INDUSTRY_EN` | Industry Name | `industry` (new) |
| `INDUSTRY_JA` | Industry Name (Japanese Language) | `industry` (new) |
| `IPADDRESS.IPV4` | IP V4 Address | `ipv4` |
| `IPADDRESS.IPV6` | IP V6 Address | `ipv6` |
| `JOB_TITLE_EN` | Job Title/Occupation (English Language) | `jobtitle` |
| `JOB_TITLE_JA` | Job Title (Japanese Language) | `jobtitle` |
| `LANGUAGE.ISO-639-1` | Language code - ISO 639, two character | `iso639_1` (new) |
| `LANGUAGE.ISO-639-2` | Language code - ISO 639, three character | `iso639_2` (new) |
| `LANGUAGE.TEXT_CS` | Language name (Czech) | `language` (new) |
| `LANGUAGE.TEXT_DA` | Language name (Danish) | `language` (new) |
| `LANGUAGE.TEXT_DE` | Language name (German) | `language` (new) |
| `LANGUAGE.TEXT_EN` | Language name, e.g. English, French, ... | `language` (new) |
| `LANGUAGE.TEXT_ES` | Language name (Spanish) | `language` (new) |
| `LANGUAGE.TEXT_FI` | Language name (Finnish) | `language` (new) |
| `LANGUAGE.TEXT_FR` | Language name (French) | `language` (new) |
| `LANGUAGE.TEXT_IT` | Language name (Italian) | `language` (new) |
| `LANGUAGE.TEXT_JA` | Language name (Japanese) | `language` (new) |
| `LANGUAGE.TEXT_NL` | Language name (Dutch) | `language` (new) |
| `LANGUAGE.TEXT_PL` | Language name (Polish) | `language` (new) |
| `LANGUAGE.TEXT_PT` | Language name (Portuguese) | `language` (new) |
| `LANGUAGE.TEXT_RO` | Language name (Romanian) | `language` (new) |
| `LANGUAGE.TEXT_RU` | Language name (Russian) | `language` (new) |
| `LANGUAGE.TEXT_SV` | Language name (Swedish) | `language` (new) |
| `MACADDRESS` | MAC Address | `mac_address` |
| `MONTH.ABBR_<LOCALE>` | Month Abbreviation <LOCALE> = Locale, e.g. en-US for English language in US) | `month` |
| `MONTH.DIGITS` | Numeric Month | `month` |
| `MONTH.FULL_<LOCALE>` | Full Month name <LOCALE> = Locale, e.g. en-US for English language in US) | `month` |
| `NAME.FIRST` | First Name | `person_firstname` |
| `NAME.FIRST_LAST` | Merged Name (First Last) | `person_fullname` |
| `NAME.LAST` | Last Name | `person_surname` |
| `NAME.LAST_FIRST` | Merged Name (Last, First) | `person_fullname` |
| `NAME.MIDDLE` | Middle Name | `person_midname` |
| `NAME.MIDDLE_INITIAL` | Middle Initial | `person_midname` |
| `NAME.SUFFIX` | Name Suffix | `namesuffix` |
| `NATIONALITY_EN` | Nationality (English Language) | `ennationality` |
| `NATIONALITY_JA` | Nationality (Japanese Language) | `nationality` |
| `NATIONALITY_NL` | Nationality (Dutch Language) | `nationality` |
| `PERIOD.HALF` | Half (Year) | `half_year` (new) |
| `PERIOD.QUARTER` | Quarter (Year) | `quarter` |
| `PERIOD.YEAR_RANGE` | Year Range | `year_range` (new) |
| `PERSON.AGE` | Age (person) | `age` |
| `PERSON.AGE_RANGE` | Age range (person) | `age_range` (new) |
| `PERSON.DATE_OF_BIRTH` | Person - Date of Birth | `birthday` |
| `PERSON.MARITAL_STATUS_EN` | Marital Status (person) | `marital_status` (new) |
| `PERSON.MARITAL_STATUS_JA` | Marital Status (Japanese Language) | `marital_status` (new) |
| `PERSON.RACE_ABBR_EN` | Race/Ethnicity (person) | `race_ethnicity` (new) |
| `PERSON.RACE_EN` | Race/Ethnicity (person) | `race_ethnicity` (new) |
| `PERSON.YEAR_OF_BIRTH` | Person - Year of Birth | `birth_year` (new) |
| `POSTAL_CODE.POSTAL_CODE_AT` | Postal Code (AT) | `at_postcode` (new) |
| `POSTAL_CODE.POSTAL_CODE_AU` | Postal Code (AU) | `au_postcode` (new) |
| `POSTAL_CODE.POSTAL_CODE_BG` | Postal Code (BG) | `bg_postcode` (new) |
| `POSTAL_CODE.POSTAL_CODE_BR` | Postal Code (BR) | `br_postcode` (new) |
| `POSTAL_CODE.POSTAL_CODE_CA` | Postal Code (CA) | `ca_postcode` (new) |
| `POSTAL_CODE.POSTAL_CODE_CH` | Postal Code (CH) | `ch_postcode` (new) |
| `POSTAL_CODE.POSTAL_CODE_CO` | Postal Code (CO) | `co_postcode` (new) |
| `POSTAL_CODE.POSTAL_CODE_DE` | Postal Code (DE) | `de_postcode` |
| `POSTAL_CODE.POSTAL_CODE_DK` | Postal Code (DK) | `dk_postcode` (new) |
| `POSTAL_CODE.POSTAL_CODE_ES` | Postal Code (ES) | `espostcode` |
| `POSTAL_CODE.POSTAL_CODE_FI` | Postal Code (FI) | `fi_postcode` (new) |
| `POSTAL_CODE.POSTAL_CODE_FR` | Postal Code (FR) | `frpostcode` |
| `POSTAL_CODE.POSTAL_CODE_IN` | Postal Code (IN) | `in_postcode` (new) |
| `POSTAL_CODE.POSTAL_CODE_IT` | Postal Code (IT) | `it_postcode` (new) |
| `POSTAL_CODE.POSTAL_CODE_JP` | Postal Code (JP) | `jp_postcode` (new) |
| `POSTAL_CODE.POSTAL_CODE_MX` | Postal Code (MX) | `mx_postcode` (new) |
| `POSTAL_CODE.POSTAL_CODE_NL` | Postal Code (NL) | `nl_postcode` |
| `POSTAL_CODE.POSTAL_CODE_NO` | Postal Code (NO) | `no_postcode` (new) |
| `POSTAL_CODE.POSTAL_CODE_PL` | Postal Code (PL) | `plpostcode` |
| `POSTAL_CODE.POSTAL_CODE_PT` | Postal Code (PT) | `pt_postcode` (new) |
| `POSTAL_CODE.POSTAL_CODE_RO` | Postal Code (RO) | `ro_postcode` (new) |
| `POSTAL_CODE.POSTAL_CODE_RU` | Postal Code (RU) | `ruspostalcode` |
| `POSTAL_CODE.POSTAL_CODE_SE` | Postal Code (SE) | `se_postcode` (new) |
| `POSTAL_CODE.POSTAL_CODE_UK` | Postal Code (UK) | `ukpostalcode` |
| `POSTAL_CODE.POSTAL_CODE_UY` | Postal Code (UY) | `uy_postcode` (new) |
| `POSTAL_CODE.ZIP5_PLUS4_US` | Postal Code + 4 (US) | `uszipcode` |
| `POSTAL_CODE.ZIP5_US` | Postal Code (US) | `uszipcode` |
| `SPATIAL.GEOJSON` | coordinate reference systems - GEOJSON | `geojson` (new) |
| `SPATIAL.WKT` | coordinate reference systems - Well-known Text | `wkt` (new) |
| `SSN` | Social Security Number (US) | `usssn` |
| `STATE_PROVINCE.CANTON_CH` | Swiss CANTON Code | `ch_canton_code` (new) |
| `STATE_PROVINCE.CANTON_NAME_CH` | Swiss CANTON Name | `ch_canton` (new) |
| `STATE_PROVINCE.COMMUNE_IT` | Italian Commune | `it_comune` (new) |
| `STATE_PROVINCE.COUNTY_FIPS_US` | US County FIPS code | `fips64` |
| `STATE_PROVINCE.COUNTY_HU` | Hungarian County | `hu_county` (new) |
| `STATE_PROVINCE.COUNTY_IE` | Irish County | `ie_county` (new) |
| `STATE_PROVINCE.COUNTY_UK` | United Kingdom County Name | `gb_county` (new) |
| `STATE_PROVINCE.COUNTY_US` | US County Name | `uscounty` |
| `STATE_PROVINCE.DEPARTMENT_CO` | Colombian Department | `co_department` (new) |
| `STATE_PROVINCE.DEPARTMENT_NAME_FR` | French Department | `fr_department` |
| `STATE_PROVINCE.DISTRICT_NAME_IN` | Indian District name | `district` |
| `STATE_PROVINCE.DISTRICT_NAME_PT` | Portuguese District Name | `pt_district` (new) |
| `STATE_PROVINCE.INSEE_CODE_FR` | French Insee Code (5 digit) | `inseecode` |
| `STATE_PROVINCE.MUNICIPALITY_BR` | Brazilian Municipality | `br_municipality` (new) |
| `STATE_PROVINCE.MUNICIPALITY_CO` | Colombian Municipality | `co_municipality` (new) |
| `STATE_PROVINCE.MUNICIPALITY_CODE_BR` | Brazilian Municipality code | `br_municipality_code` (new) |
| `STATE_PROVINCE.MUNICIPALITY_CODE_NL` | Dutch Municipality Code | `nl_municipality_code` (new) |
| `STATE_PROVINCE.MUNICIPALITY_MX` | Mexican Municipality | `mx_municipality` (new) |
| `STATE_PROVINCE.MUNICIPALITY_NL` | Dutch Municipality | `nl_municipality` (new) |
| `STATE_PROVINCE.PREFECTURE_CODE_JA` | Japanese Prefecture JIS X 0401 Code | `jp_prefecture_code` (new) |
| `STATE_PROVINCE.PREFECTURE_ISO_JA` | Japanese Prefecture ISO 3166-2 Code | `iso3166code` |
| `STATE_PROVINCE.PREFECTURE_NAME_JA` | Japanese Prefecture Name | `prefecture` |
| `STATE_PROVINCE.PROVINCE_CA` | Canadian Province Code | `caprovincecode` |
| `STATE_PROVINCE.PROVINCE_IT` | Italian Province Code | `it_province_code` (new) |
| `STATE_PROVINCE.PROVINCE_NAME_CA` | Canadian Province Name | `caprovince` |
| `STATE_PROVINCE.PROVINCE_NAME_EC` | Ecuadorian Province Name | `ec_province` (new) |
| `STATE_PROVINCE.PROVINCE_NAME_ES` | Spanish Province Name | `es_province` (new) |
| `STATE_PROVINCE.PROVINCE_NAME_IE` | Irish Province | `ie_province` (new) |
| `STATE_PROVINCE.PROVINCE_NAME_IT` | Italian Province Name | `it_province` (new) |
| `STATE_PROVINCE.PROVINCE_NAME_NL` | Netherlands Province Name | `nl_province` (new) |
| `STATE_PROVINCE.PROVINCE_NAME_PE` | Peruvian Province | `pe_province` (new) |
| `STATE_PROVINCE.PROVINCE_NAME_ZA` | South African Province Name | `za_province` (new) |
| `STATE_PROVINCE.PROVINCE_ZA` | South African Province Code | `za_province_code` (new) |
| `STATE_PROVINCE.REGION_NAME_FR` | French Region | `fr_region` |
| `STATE_PROVINCE.REGION_NAME_IT` | Italian Region | `it_region` (new) |
| `STATE_PROVINCE.REGION_NAME_JA` | Japanese Prefecture Region | `jp_region` (new) |
| `STATE_PROVINCE.REGION_NAME_PE` | Peruvian Region/Department | `pe_region` (new) |
| `STATE_PROVINCE.REGION_NAME_TZ` | Tanzanian Region | `tz_region` (new) |
| `STATE_PROVINCE.STATE_AU` | Australian State Code | `au_state_code` (new) |
| `STATE_PROVINCE.STATE_BR` | Brazilian State Code | `br_state_code` (new) |
| `STATE_PROVINCE.STATE_FIPS_US` | US State FIPS code | `fips52` |
| `STATE_PROVINCE.STATE_MX` | Mexican State Code | `iso3166_mx3a` |
| `STATE_PROVINCE.STATE_NAME_AU` | Australian State Name | `au_state` (new) |
| `STATE_PROVINCE.STATE_NAME_BR` | Brazilian State Name | `br_state` (new) |
| `STATE_PROVINCE.STATE_NAME_DE` | German State Name | `de_state` (new) |
| `STATE_PROVINCE.STATE_NAME_MX` | Mexican State Name | `mxstate` |
| `STATE_PROVINCE.STATE_NAME_US` | US State Name | `usstate` |
| `STATE_PROVINCE.STATE_PROVINCE_NA` | US State Code/Canadian Province Code/Mexican State Code | not mapped |
| `STATE_PROVINCE.STATE_PROVINCE_NAME_NA` | US State Name/Canadian Province Name/Mexican State Name | not mapped |
| `STATE_PROVINCE.STATE_UNION_IN` | Indian State/Union Code | `state` |
| `STATE_PROVINCE.STATE_UNION_NAME_IN` | Indian State/Union name | `state` |
| `STATE_PROVINCE.STATE_US` | US State Code | `usstate` |
| `STATE_PROVINCE.SUBURB_AU` | Australian Suburb | `au_suburb` (new) |
| `STREET_ADDRESS2_EN` | Street Address - Line 2 (English Language) | `address_line2` (new) |
| `STREET_ADDRESS3_EN` | Street Address - Line 3 (English Language) | `address_line2` (new) |
| `STREET_ADDRESS4_EN` | Street Address - Line 4 (English Language) | `address_line2` (new) |
| `STREET_ADDRESS_<LANGUAGE>` | Street Address | `street_address` (new) |
| `STREET_ADDRESS_EN` | Street Address (English Language) | `street_address` (new) |
| `STREET_ADDRESS_JA` | Street Address (Japanese) | `address` |
| `STREET_MARKER_EN` | Street Marker (English Language) | `street_suffix` (new) |
| `STREET_NAME_BARE_<LANGUAGE>` | Street Address | `street` |
| `STREET_NAME_BARE_EN` | Street Name - no Marker (English Language) | `street` |
| `STREET_NAME_EN` | Street Name (English Language) | `street` |
| `STREET_NUMBER` | Street Number | `buildingnumber` |
| `TELEPHONE` | Telephone Number (Generic) | `phone` |
| `TIMEZONE.IANA` | IANA Time Zone (Olson) | `ianatimezoneid` |
| `URI.URL` | URL - see RFC 3986 | `url` |
| `VIN` | Vehicle Identification Number | `vin` |
