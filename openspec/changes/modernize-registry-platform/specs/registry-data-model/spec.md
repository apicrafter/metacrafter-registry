## Purpose

This capability defines the source record contract for datatypes, patterns and
tools, and for the reference lists that support them. It is the contract that
every human or agent contributor and every build step relies on.

## ADDED Requirements

### Requirement: One YAML file per entity, named by ID
Each datatype, pattern and tool SHALL be stored as a single YAML file named `<id>.yaml`.

- Datatypes and patterns SHALL be stored under `data/datatypes/<COUNTRY|any>/<category>/`.
- Tools SHALL be stored under `data/tools/<category>/`.
- IDs SHALL match `^[a-z0-9_]+$`.
- An ID SHALL be unique across all datatypes, patterns, tools and aliases.

#### Scenario: File name differs from ID
- **WHEN** a file `us_ssn.yaml` declares `id: usssn`
- **THEN** validation fails with an error that names the file and the expected file name `usssn.yaml`

#### Scenario: ID collides with an alias
- **WHEN** a new record declares an `id` that another record lists in `aliases`
- **THEN** validation fails and reports both records

### Requirement: Published JSON Schema
The record contract SHALL be expressed as JSON Schema (draft 2020-12). There SHALL be one schema each for datatype, pattern and tool records. The schemas SHALL be published with the site so that external tools can validate records.

#### Scenario: Editor validation
- **WHEN** a contributor opens a datatype YAML file in an editor that supports JSON Schema
- **THEN** the editor can resolve the published schema and report invalid fields

### Requirement: Typed core fields
Records SHALL use these types:

- `is_pii` SHALL be a boolean.
- `parent` SHALL be a datatype ID string.
- `categories`, `country` and `langs` SHALL be lists of IDs that exist in the reference lists.
- A field without a value SHALL be omitted. Empty strings and empty lists SHALL NOT be used.

#### Scenario: String boolean rejected
- **WHEN** a record contains `is_pii: 'True'`
- **THEN** schema validation fails for `is_pii`

#### Scenario: Empty placeholder rejected
- **WHEN** a record contains `regexp: ''` or `examples: []`
- **THEN** validation fails and asks for the field to be removed

### Requirement: Lifecycle status
Every datatype and pattern SHALL have a `status` of `draft`, `stable` or `deprecated`.

- A `deprecated` record SHALL name its successor in `replaced_by`, unless it has no successor.
- Records created by generator scripts SHALL be created as `draft`.

#### Scenario: Deprecated without successor reference
- **WHEN** a record has `status: deprecated` and a `replaced_by` that does not resolve to an existing ID
- **THEN** validation fails

#### Scenario: Generated stub
- **WHEN** a generator script creates a record from a metacrafter-rules key
- **THEN** the record has `status: draft`

### Requirement: Permanent aliases for retired IDs
When an ID is retired, for example because duplicate records were merged, the surviving record SHALL list the retired ID in `aliases`.

An ID that has been published SHALL NOT be removed unless it remains resolvable as an alias.

#### Scenario: Merge of duplicates
- **WHEN** record `ssn` is merged into `usssn`
- **THEN** `usssn` lists `ssn` in `aliases` and no file with `id: ssn` remains

### Requirement: Examples with validity
Examples SHALL be objects with a `value`. They MAY have a `description`. They MAY have a boolean `valid`, which defaults to `true`.

When a record has a `regexp`, these rules apply:

- Every example with `valid: true` SHALL match the regexp.
- Every example with `valid: false` SHALL NOT match the regexp, unless the record also defines a `checksum` that rejects the value.

#### Scenario: Positive example fails regexp
- **WHEN** record `isni` has regexp `(\d{4})(\d{4})(\d{4})(\d{4})` and the example `0000 0001 2197 5163`
- **THEN** validation fails and reports the record, the example and the regexp

#### Scenario: Negative example
- **WHEN** an example has `valid: false` and its value matches the regexp, and the record has no checksum
- **THEN** validation fails

### Requirement: Typed mappings to external vocabularies
A record MAY declare `mappings` with these keys: `wikidata`, `schema_org`, `dpv`, `presidio`, `google_dlp`, `purview`, `d3m`, `sherlock`, `cdm`, `fta`, `autotype`, `gs1_ai`, `orgid`, `qddate`, `bioregistry`, `stdnum` and `fhir`. Each key SHALL hold a single identifier or a list of identifiers in that system's native format.

`mappings.wikidata` SHALL match `^[PQ]\d+$`.

#### Scenario: Wikidata given as URL
- **WHEN** a record has `mappings: {wikidata: "https://www.wikidata.org/wiki/Property:P968"}`
- **THEN** validation fails and expects `P968`

`mappings.cdm` SHALL hold Microsoft Common Data Model trait names, such as `means.identity.service.email`, and not CDM data type or entity names.

#### Scenario: CDM data type name instead of a trait
- **WHEN** a record has `mappings: {cdm: "email"}`
- **THEN** validation fails with a schema error on `mappings.cdm`

`mappings.d3m` SHALL hold D3M semantic type URIs as D3M metadata writes them: `https://metadata.datadrivendiscovery.org/types/<Name>` or `http://schema.org/<Name>`. D3M column roles (such as `PrimaryKey` or `Target`) SHALL NOT be mapped, because they do not say what a value means.

#### Scenario: D3M type given as a bare name
- **WHEN** a record has `mappings: {d3m: "FileName"}`
- **THEN** validation fails with a schema error on `mappings.d3m`

`mappings.fta` SHALL hold FTA (Fast Text Analysis) semantic types as FTA documents them, such as `EMAIL` or `COUNTRY.ISO-3166-2`. A locale-bound type keeps FTA's placeholder (`MONTH.FULL_<LOCALE>`), except `IDENTITY.VAT_<COUNTRY>`, whose bound names (`IDENTITY.VAT_FR`) map to different records. `crosswalk("fta", ...)` SHALL resolve a bound name, such as `MONTH.FULL_fr-FR`, through its placeholder when no record has the exact name.

#### Scenario: FTA type in lowercase
- **WHEN** a record has `mappings: {fta: "email"}`
- **THEN** validation fails with a schema error on `mappings.fta`

#### Scenario: Locale-bound FTA type
- **WHEN** a client calls `crosswalk("fta", "GENDER.TEXT_DE")`
- **THEN** it gets the record that maps `GENDER.TEXT_<LANGUAGE>`

`mappings.sherlock` SHALL hold one or more of the 78 Sherlock semantic type labels, spelled as the trained Sherlock model returns them (for example `city` or `birth Date`). A Sherlock type SHALL be mapped to at most one record, and only when that record has the same meaning. The `sherlock` tool SHALL list exactly the records that carry `mappings.sherlock`. Sato predicts the same 78 types in camelCase (`birthDate`), so the registry SHALL NOT add a separate Sato mapping key: the `sato` tool SHALL list the same records as the `sherlock` tool, and `crosswalk("sato", label)` SHALL resolve through `mappings.sherlock`.

#### Scenario: Unknown Sherlock label
- **WHEN** a record has `mappings: {sherlock: "email"}`
- **THEN** validation fails with a schema error on `mappings.sherlock`

`mappings.autotype` SHALL hold AutoType benchmark test case names: the names of the benchmark's `data_release/*.txt` files without the `.txt` extension, such as `isbn` or `date-chinese`. A test case SHALL map to at most one record.

#### Scenario: AutoType test case given as a file name
- **WHEN** a record has `mappings: {autotype: "isbn.txt"}`
- **THEN** validation fails with a schema error on `mappings.autotype`

`mappings.gs1_ai` SHALL hold GS1 Application Identifiers as GS1 writes them: two to four digits with their leading zeros, as strings (`01`, `414`, `8003`). A GS1 AI SHALL be mapped to at most one record: the record of the AI's element string when the registry has one, otherwise the record of the value that the AI carries. `crosswalk("gs1_ai", ...)` SHALL also accept the AI in parentheses, as printed under a barcode, and its `https://ref.gs1.org/ai/` IRI.

#### Scenario: GS1 AI without its leading zero
- **WHEN** a record has `mappings: {gs1_ai: 1}`
- **THEN** validation fails with a schema error on `mappings.gs1_ai`

#### Scenario: GS1 AI from a barcode's human-readable text
- **WHEN** a client calls `crosswalk("gs1_ai", "(8003)")`
- **THEN** it gets the record `gs1_ai_8003`, whose `semantic_type` is `grai`

`mappings.orgid` SHALL hold ORG-ID.guide list codes, such as `GB-COH` or `CA_ON-ONT`, of the organization identifier lists whose identifiers the record describes. A list code SHALL be mapped to at most one record. A deprecated code MAY be mapped when ORG-ID.guide names the list that replaced it and both lists use the same identifier. `crosswalk("orgid", ...)` SHALL accept a list code in any case, its `https://org-id.guide/list/<code>` URL or a whole ORG-ID.guide identifier such as `GB-COH-09506232`.

#### Scenario: ORG-ID.guide identifier instead of a list code
- **WHEN** a record has `mappings: {orgid: "GB-COH-09506232"}`
- **THEN** validation fails with a schema error on `mappings.orgid`

#### Scenario: Crosswalk from a whole identifier
- **WHEN** a client calls `crosswalk("orgid", "GB-COH-09506232")`
- **THEN** it gets the record that maps `GB-COH`

`mappings.qddate` SHALL hold keys of qddate date patterns, such as `dt:date:date_2`, as qddate defines them and as metacrafter reports them in the `format` of a date match. A key SHALL be mapped to at most one record that describes the same notation: `date` itself (whose regexp is the ISO 8601 form) or a pattern of `date` or `monthday`. The keys of generated variants (`dt:date:date_2:time_1`, `...:t_right`) SHALL NOT be mapped; `crosswalk("qddate", ...)` SHALL resolve such a key to the record of its base pattern, and SHALL accept a key without its `dt:date:` prefix. The `qddate` tool SHALL list exactly the records that carry `mappings.qddate`.

#### Scenario: Generated qddate variant in a mapping
- **WHEN** a record has `mappings: {qddate: "dt:date:date_2:time_1"}`
- **THEN** validation fails with a schema error on `mappings.qddate`

#### Scenario: Crosswalk from a date with a time
- **WHEN** a client calls `crosswalk("qddate", "dt:date:date_2:time_1")`
- **THEN** it gets the record that maps `dt:date:date_2`, the notation of the date part

`mappings.bioregistry` SHALL hold normalized, lowercase Bioregistry prefixes (`chebi`, `ncbitaxon`) of the identifier resources whose local identifiers the record describes. `crosswalk("bioregistry", ...)` SHALL accept a prefix in any case, its bioregistry.io URL or a CURIE (`CHEBI:15377`).

#### Scenario: Crosswalk from a CURIE
- **WHEN** a client calls `crosswalk("bioregistry", "CHEBI:15377")`
- **THEN** it gets the record that maps `chebi`

`mappings.stdnum` SHALL hold python-stdnum module paths without the `stdnum.` prefix (`br.cpf`, `iban`, `in_.aadhaar`) of the modules that validate the record's identifier. `crosswalk("stdnum", ...)` SHALL also accept the module with its prefix, a file path (`br/cpf`) or the module's documentation URL.

#### Scenario: stdnum module with its package prefix
- **WHEN** a record has `mappings: {stdnum: "stdnum.br.cpf"}`
- **THEN** validation fails with a schema error on `mappings.stdnum`; the record must write `br.cpf`

#### Scenario: Crosswalk from a full module name
- **WHEN** a client calls `crosswalk("stdnum", "stdnum.br.cpf")`
- **THEN** it gets the record that maps `br.cpf`

`mappings.fhir` SHALL hold HL7 FHIR identifier system URIs (`Identifier.system`) as HL7 Terminology or the base implementation guide of a national HL7 affiliate publishes them: an http(s) URI (`http://hl7.org/fhir/sid/us-ssn`), an OID URN (`urn:oid:2.16.840.1.113883.4.1`) or another URN (`urn:dicom:uid`).

#### Scenario: FHIR system without a scheme
- **WHEN** a record has `mappings: {fhir: "hl7.org/fhir/sid/us-ssn"}`
- **THEN** validation fails with a schema error on `mappings.fhir`

### Requirement: Pattern inheritance
A pattern SHALL reference an existing datatype through `semantic_type`.

A pattern SHALL inherit `categories`, `is_pii` and `classification` from that datatype. It does not inherit a field that it declares explicitly.

#### Scenario: Pattern without categories
- **WHEN** a pattern omits `categories` and its datatype has `categories: [pii, persons]`
- **THEN** every published representation of the pattern lists `pii` and `persons`

### Requirement: Explicit reference lists
Countries SHALL use ISO 3166-1 alpha-2 codes. Each country entry SHALL have a `kind` of `country` or `region`; `EU` has `kind: region`.

Languages SHALL use ISO 639-1 codes. Each language entry SHALL have a `kind` of `language` or `special`; `common` means language-independent and has `kind: special`.

A code SHALL NOT be used with a meaning that differs from its ISO meaning.

#### Scenario: Swedish language code
- **WHEN** a record lists Swedish as `se`
- **THEN** validation fails, because `se` is Northern Sami, and suggests `sv`

### Requirement: Directory and country consistency
A record under `data/datatypes/<CC>/` SHALL include `<CC>` in `country`.

A record under `data/datatypes/any/` SHALL either have no `country`, or list two or more countries.

#### Scenario: Wrong country in directory
- **WHEN** `data/datatypes/US/finances/us_bankaccount.yaml` declares `country: [RU]`
- **THEN** validation fails
