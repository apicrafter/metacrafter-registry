## Purpose

This capability groups datatypes into curated, named packs for one purpose,
such as "Russian personal data". A consumer selects a pack by id and gets its
datatypes, patterns and the metacrafter-rules rules that detect them.

## ADDED Requirements

### Requirement: Pack source records
Each pack SHALL be one YAML file `data/packs/<id>.yaml`, valid against `schema/pack.schema.json`. A pack SHALL have `id`, `name`, `doc` and `status`, and at least one of `datatypes` and `select`. It MAY have `exclude`, `translations` and, when deprecated, `replaced_by`.

- `id` SHALL match `[a-z0-9_]+`, SHALL equal the file name without `.yaml`, and SHALL be unique among packs.
- `status` SHALL be `draft`, `stable` or `deprecated`.
- Empty values SHALL NOT be allowed, and unknown fields SHALL be rejected.

#### Scenario: Valid pack
- **WHEN** `data/packs/ru_pii.yaml` has `id: ru_pii`, a name, a description, `status: draft` and a `select` filter
- **THEN** `metacrafter-registry validate` reports no error for it

#### Scenario: File name differs from id
- **WHEN** `data/packs/ru_pii.yaml` has `id: russian_pii`
- **THEN** validation fails and names the file and both ids

### Requirement: Pack membership
The member datatypes of a pack SHALL be the ids in `datatypes`, plus the datatypes that match `select`, minus the ids in `exclude`. A pattern SHALL be a member when the datatype named by its `semantic_type` is a member.

`select` SHALL accept the keys `categories`, `country`, `langs`, `is_pii`, `classification`, `checksum` and `status`. Keys SHALL combine with AND, and the values of one list SHALL combine with OR. The `country` value `any` SHALL match datatypes that have no country. `checksum: true` SHALL match datatypes that have a `checksum`. When `status` is absent, `select` SHALL match only `stable` datatypes. `select` SHALL never match a `deprecated` datatype.

#### Scenario: Filter and hand-picked id
- **WHEN** a pack has `select: {country: [RU], is_pii: true}` and `datatypes: [inn]`
- **THEN** its members are every stable RU datatype with `is_pii: true`, plus `inn`

#### Scenario: Drafts stay out of filters
- **WHEN** a new `draft` datatype matches a pack's `select` filter, and the filter has no `status` key
- **THEN** the datatype is not a member of the pack

#### Scenario: Patterns follow their datatype
- **WHEN** `email` is a member and a pattern has `semantic_type: email`
- **THEN** the pattern is listed in the pack's `patterns`

### Requirement: Pack validation gates
The build SHALL fail, and write nothing, when:

- an id in `datatypes` or `exclude` is unknown, is a pattern, or is an alias. For an alias, the error SHALL name the canonical id;
- a `select` value is not a known category, country, language or classification;
- a pack has no members after resolution;
- `replaced_by` does not name another pack.

The build SHALL warn when `datatypes` lists a `draft` or `deprecated` datatype, when an `exclude` id would not be a member anyway, and when a `stable` pack has a member that no metacrafter-rules rule detects.

#### Scenario: Alias in a pack
- **WHEN** a pack lists a retired id in `datatypes`
- **THEN** the build fails and the error names the record the alias resolves to

#### Scenario: Empty pack
- **WHEN** a pack's filter matches nothing and it lists no ids
- **THEN** the build fails and names the pack

### Requirement: Pack API files
The site SHALL serve `/api/v1/packs.json` and one `/api/v1/packs/<id>.json` per pack.

- `/api/v1/packs.json` SHALL list every pack with `id`, `name`, `status`, `counts` (datatypes, patterns, rules) and the pack's absolute URLs.
- `/api/v1/packs/<id>.json` SHALL contain the pack's source fields and the resolved `datatypes`, `patterns`, `rules` and `without_rules`, the metacrafter-rules commit as `rules_ref`, and the pack's absolute URLs.
- Each entry in `rules` SHALL be a metacrafter-rules rule whose `key` is a member or an alias of a member, with the fields `rule`, `key`, `type`, `context`, `lang`, `country_code` and `file` from the pinned coverage file.
- All id lists SHALL be sorted, so two builds of the same sources produce identical files.
- The manifest SHALL list both kinds of file with size and SHA-256, and the OpenAPI description SHALL describe them.

#### Scenario: Fetch one pack
- **WHEN** a client requests `/api/v1/packs/ru_pii.json`
- **THEN** the response lists the member datatype ids, the pattern ids, the rules with their `key` and `context`, and `rules_ref`

### Requirement: Records list their packs
Each datatype and pattern in `/api/v1/` SHALL have a `packs` field with the sorted ids of the packs it belongs to, omitted when there are none. The legacy files `/registry.json`, `/datatype/<id>.json`, `/tools.json` and `/tool/<id>.json` SHALL NOT change.

#### Scenario: Member record
- **WHEN** `rusnils` is a member of `ru_pii`
- **THEN** `/api/v1/datatypes/rusnils.json` has `"packs": ["ru_pii"]`

#### Scenario: Legacy file unchanged
- **WHEN** packs are added
- **THEN** `/datatype/rusnils.json` has the same fields as before

### Requirement: Pack pages
The site SHALL serve `/pack/` with every pack, and `/pack/<id>` with the pack's description, how its membership is defined, its members and its rule coverage. Each pack page SHALL have a Markdown twin at `/pack/<id>.md`. A record page SHALL link to the packs the record belongs to. The sitemap and `llms.txt` SHALL list the pack pages.

#### Scenario: Pack page
- **WHEN** a user opens `/pack/ru_pii`
- **THEN** the page shows the filter in words, the hand-picked ids, the member table and the number of members without rules

### Requirement: Stable pack URLs
Pack URLs SHALL be part of the URL contract. A published pack SHALL NOT be deleted or renamed. A retired pack SHALL be marked `deprecated`, SHALL keep its pages and API file, and MAY name `replaced_by`. The URL contract check SHALL cover `/pack/`, `/api/v1/packs.json` and one pack from the sources.

#### Scenario: Deprecated pack
- **WHEN** a pack is marked `deprecated` with `replaced_by: ru_pii_v2`
- **THEN** `/pack/<old id>` and `/api/v1/packs/<old id>.json` still resolve, and both name `ru_pii_v2`

### Requirement: Pack changes in the changelog
The changelog between two data versions SHALL report added, deprecated and changed packs. For a changed pack, it SHALL list the datatypes that joined and left it.

#### Scenario: Record joins a filter pack
- **WHEN** a datatype becomes `stable` and so matches a pack's filter
- **THEN** `/api/v1/changes.json` for the release lists the datatype as joining that pack
