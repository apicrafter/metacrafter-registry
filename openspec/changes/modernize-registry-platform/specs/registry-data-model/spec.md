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
A record MAY declare `mappings` with these keys: `wikidata`, `schema_org`, `dpv`, `presidio`, `google_dlp`, `purview`, `d3m`, `sherlock`, `cdm` and `autotype`. Each key SHALL hold a single identifier or a list of identifiers in that system's native format.

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

`mappings.autotype` SHALL hold AutoType benchmark test case names: the names of the benchmark's `data_release/*.txt` files without the `.txt` extension, such as `isbn` or `date-chinese`. A test case SHALL map to at most one record.

#### Scenario: AutoType test case given as a file name
- **WHEN** a record has `mappings: {autotype: "isbn.txt"}`
- **THEN** validation fails with a schema error on `mappings.autotype`

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
