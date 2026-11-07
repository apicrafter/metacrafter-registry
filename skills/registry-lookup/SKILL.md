---
name: registry-lookup
description: Label the columns of a dataset with semantic datatypes from the Metacrafter Registry (identifiers, personal data, codes) and decide which fields are PII. Use when asked what a column contains, whether a field is personal data, to classify or document a table, or to map a type to Presidio, Wikidata or another vocabulary.
---

# Label data with the Metacrafter Registry

The Metacrafter Registry (https://registry.apicrafter.io) describes semantic
datatypes: what a value means. Each record has an id, a description, a PII flag,
categories, countries, and often a regular expression, a check-digit algorithm,
examples and links. Every record has a stable URL,
`https://registry.apicrafter.io/datatype/<id>`, that you can cite.

## Choose an access method

1. **MCP tools** (best): if the `metacrafter-registry` MCP server is connected,
   use its tools. They run locally, so sample values are not sent anywhere.
2. **Python**: `pip install metacrafter-registry`, then
   `from metacrafter_registry import Registry; reg = Registry.fetch()`.
3. **HTTP** (no install): read `https://registry.apicrafter.io/llms.txt`, a
   record as Markdown at `/datatype/<id>.md`, or JSON at
   `/api/v1/datatypes/<id>.json`. Do not send real personal data to any web
   service; describe the format instead.

## Label a column

For each column:

1. Take up to 20 non-empty sample values and the column name.
2. Call `identify_values(values, field_name, country)`, or
   `reg.identify(values, field_name=..., country=...)`. Pass `country` (ISO
   3166-1 alpha-2) when you know where the data comes from.
3. Read the top candidates:
   - `score` is 0-100. A score of 80 or more, with a `regexp_hit_rate` near 1,
     is a strong match.
   - `checksum.pass_rate` of 1.0 is near-certain evidence (IBAN, INN, card
     numbers, ISBN). A low pass rate rules a type out even if the regexp
     matches.
   - `regexp_specificity` is low for catch-all patterns, so their hits mean
     little.
   - Some types share a format: SHA-256, Keccak-256 and BLAKE2b-256 are all 64
     hex digits. Then the field name and context decide; say so.
4. If nothing scores above about 50, use `search_datatypes` with words from the
   column name, or report the column as unknown. Do not force a match.
5. Check `status`. `draft` records have not been reviewed. You may use them,
   but say "draft" and do not base compliance decisions on them alone.

## Report

For each column, give:
- the id
- the name
- whether it is PII
- your confidence and the evidence: hit rate, checksum, field name
- the record URL from the result's `url`

Example:

| Column | Datatype | PII | Evidence |
|---|---|---|---|
| `inn` | [Russian INN](https://registry.apicrafter.io/datatype/inn) (`inn`) | no | 100% regexp, 100% INN check digit, field name |

## Other tasks

- **"Is this PII?"** The record's `is_pii` is the registry's answer. Categories
  such as `pii` and `persons` add context.
- **Crosswalk.** `crosswalk("wikidata", "P968")` finds the registry record for
  an id in another vocabulary. The systems are `wikidata`, `fibo`, `schema_org`,
  `dpv`, `presidio`, `google_dlp`, `purview`, `d3m`, `sherlock`, `sato`, `cdm`, `fta`,
  `autotype` (AutoType benchmark test cases, such as `isbn` or `date-chinese`),
  `gs1_ai`, `orgid` (ORG-ID.guide list codes, such as `GB-COH`), `qddate`
  (qddate date pattern keys, such as `dt:date:date_2`), `bioregistry`
  (Bioregistry prefixes or CURIEs, such as `chebi` or `CHEBI:15377`), `stdnum`
  (python-stdnum modules, such as `br.cpf`) and `fhir` (HL7 FHIR identifier
  system URIs, such as `http://hl7.org/fhir/sid/us-ssn`).
  Coverage outside Wikidata is still small. For `fibo`, pass a FIBO class IRI,
  for example
  `https://spec.edmcouncil.org/fibo/ontology/FBC/ProductsAndServices/ClientsAndAccounts/InternationalBankAccountIdentifier`;
  it links glossary terms to registry types. For a Microsoft Common Data Model
  column, pass the meaning trait of its data type: `crosswalk("cdm",
  "means.location.postalCode")` returns `postindex`. For a D3M dataset column,
  pass a semantic type URI from its metadata: `crosswalk("d3m",
  "http://schema.org/email")` returns `email`. Column roles such as
  `.../types/PrimaryKey` or `.../types/Target` are not mapped. For a Microsoft
  Purview sensitive information type, pass its name: case, periods and
  apostrophes do not matter, former names still resolve, and a bundle such as
  "EU passport number" returns the records of all its member types. For a
  column that FTA (Fast Text Analysis) labelled, pass FTA's semantic type as it
  reports it: `crosswalk("fta", "POSTAL_CODE.ZIP5_US")` returns `uszipcode`,
  and `crosswalk("fta", "MONTH.FULL_fr-FR")` returns `month`.
  For a column that Sherlock labelled, pass its label: `crosswalk("sherlock",
  "birth Date")` returns `birthday`; case and spaces are ignored. 32 of
  Sherlock's 78 types are mapped. Generic labels such as `code`, `type` or
  `rank` return nothing. Sato predicts the same 78 types, written in camelCase:
  `crosswalk("sato", "birthDate")` also returns `birthday`.
  For an entity that Presidio found in free text, pass its name:
  `crosswalk("presidio", "LOCATION")` returns `location` and the narrower place
  records (`city`, `country`, `birthplace`, ...), whose `parent` is `location`.
  Take the returned records that have no returned ancestor: `location` for
  `LOCATION`, `orgname` for `ORGANIZATION`, `person_fullname` for `PERSON` and
  `date` for `DATE_TIME`. `NRP` returns both `nationality` and `religion`.
  For a field of a GS1 barcode, pass its Application
  Identifier: `crosswalk("gs1_ai", "(8003)")` returns `gs1_ai_8003`, the GRAI
  element string, whose `semantic_type` is `grai`; `crosswalk("gs1_ai",
  "8007")` returns `iban`. GS1 identification keys and their qualifiers are
  mapped; dates, measures and other data attributes are not.
  For an organization identifier in the ORG-ID.guide
  form, as in IATI, 360Giving or Open Contracting data, pass the list code or
  the whole identifier: `crosswalk("orgid", "GB-COH-09506232")` returns
  `companyhouseid`. A column of whole ORG-ID.guide identifiers is `org_id`; a
  column of list codes (`identifier.scheme`) is `org_id_scheme`.
  For a date column, metacrafter reports the qddate pattern that read it as
  the `format` of its `datetime` match. Pass that key to get the notation:
  `crosswalk("qddate", "dt:date:date_2")` returns `date_dmy`
  (25.12.2024), and `crosswalk("qddate", "dt:date:date_rus_lc2")` returns
  `date_russian`. A key with a time or trailing text
  (`dt:date:date_2:time_1`) resolves to the notation of its date part.
- **Former ids.** `get_datatype("ssn")` returns `usssn` with
  `resolved_from_alias`. Always cite the canonical id.
